"""Watched toggle endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_tracking_service
from app.api.schemas import WatchedIn, WatchedOut
from app.services.tracking_service import TrackingService

router = APIRouter(prefix="/episodes", tags=["tracking"])

TrackingServiceDep = Annotated[TrackingService, Depends(get_tracking_service)]


@router.put("/{episode_id}/watched", response_model=WatchedOut)
async def set_watched(
    episode_id: int,
    body: WatchedIn,
    service: TrackingServiceDep,
) -> WatchedOut:
    """Idempotently mark an episode as watched or unwatched."""
    marker = await service.set_watched(
        series_id=body.series_id,
        episode_id=episode_id,
        watched=body.watched,
    )
    return WatchedOut(
        episode_id=episode_id,
        series_id=body.series_id,
        watched=marker is not None,
        watched_at=marker.watched_at if marker else None,
    )
