"""
Security utilities: JWT creation/verification, password hashing, token revocation.
"""
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from redis import Redis

from .config import settings

bearer_scheme = HTTPBearer()

# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def _make_token(sub: str, role: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "role": role,
        "type": token_type,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def create_token_pair(username: str, role: str) -> dict:
    access = _make_token(
        username, role, "access", timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    refresh = _make_token(
        username, role, "refresh", timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
    )
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


def decode_token(token: str, expected_type: str | None = "access") -> dict:
    try:
        claims = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except JWTError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}")

    if expected_type and claims.get("type") != expected_type:
        raise HTTPException(status_code=401, detail="Wrong token type")

    _check_revoked(claims["jti"])
    return claims


# ---------------------------------------------------------------------------
# Token revocation (backed by Redis)
# ---------------------------------------------------------------------------

def _redis() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


def revoke_token(jti: str, exp: int) -> None:
    now = int(datetime.now(timezone.utc).timestamp())
    ttl = max(exp - now, 1)
    _redis().setex(f"{settings.TOKEN_REVOKE_PREFIX}:{jti}", ttl, "1")


def _check_revoked(jti: str) -> None:
    if _redis().exists(f"{settings.TOKEN_REVOKE_PREFIX}:{jti}"):
        raise HTTPException(status_code=401, detail="Token has been revoked")


# ---------------------------------------------------------------------------
# FastAPI dependency: require specific roles
# ---------------------------------------------------------------------------

def require_roles(*roles: str):
    def _dep(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
        claims = decode_token(credentials.credentials, expected_type="access")
        if claims.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return claims

    return _dep
