"""AI insight endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_insight_service
from app.api.schemas import InsightOut
from app.services.insight_service import InsightService

router = APIRouter(prefix="/series/{series_id}/insights", tags=["insights"])

InsightServiceDep = Annotated[InsightService, Depends(get_insight_service)]


@router.get("", response_model=InsightOut)
async def series_insight(
    series_id: int,
    service: InsightServiceDep,
) -> InsightOut:
    """Spoiler-free insight for the whole series."""
    return InsightOut.from_domain(await service.for_series(series_id))


@router.get("/episodes/{episode_id}", response_model=InsightOut)
async def episode_insight(
    series_id: int,
    episode_id: int,
    service: InsightServiceDep,
) -> InsightOut:
    """Spoiler-free insight for one episode."""
    insight = await service.for_episode(
        series_id=series_id,
        episode_id=episode_id,
    )
    return InsightOut.from_domain(insight)
