"""
Health check endpoints for database connectivity.
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from db.mongo import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/db", response_class=JSONResponse)
async def health_db() -> dict[str, bool]:
    """Return {"ok": True} if a ping command to MongoDB succeeds."""
    info = await get_db().command("ping")
    return {"ok": bool(info.get("ok"))}
