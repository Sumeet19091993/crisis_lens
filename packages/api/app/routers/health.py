from fastapi import APIRouter, HTTPException
from sqlalchemy import text
import redis as redis_lib

from ..config import settings
from ..db import engine

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/ready")
def ready():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"db not ready: {e}")

    try:
        url = settings.redis_url
        if url.startswith("rediss://"):
            r = redis_lib.from_url(url, decode_responses=True, ssl_cert_reqs=False)
        else:
            r = redis_lib.from_url(url, decode_responses=True)
        r.ping()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"redis not ready: {e}")

    return {"status": "ready"}
