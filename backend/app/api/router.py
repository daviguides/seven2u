"""Aggregates all API sub-routers under a single router."""

from fastapi import APIRouter

from app.api import series

api_router = APIRouter()
api_router.include_router(series.router)


@api_router.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}
