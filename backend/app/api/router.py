"""Aggregates all API sub-routers under a single router."""

from fastapi import APIRouter

from app.api import comments, insights, series, tracking

api_router = APIRouter()
api_router.include_router(series.router)
api_router.include_router(tracking.router)
api_router.include_router(comments.router)
api_router.include_router(insights.router)


@api_router.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}
