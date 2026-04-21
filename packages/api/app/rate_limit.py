import time
from fastapi import Request, HTTPException


def _client_key(request: Request) -> str:
    device = request.headers.get("x-device-id")
    if device:
        return f"device:{device}"
    ip = request.client.host if request.client else "unknown"
    return f"ip:{ip}"


async def rate_limit_dependency(request: Request):
    pass
