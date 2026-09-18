"""Series search and detail endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_series_service
from app.api.schemas import SeriesDetailOut, SeriesOut
from app.services.series_service import MAX_QUERY_LENGTH, SeriesService

router = APIRouter(prefix="/series", tags=["series"])

SeriesServiceDep = Annotated[SeriesService, Depends(get_series_service)]


@router.get("/search", response_model=list[SeriesOut])
async def search_series(
    q: Annotated[str, Query(min_length=1, max_length=MAX_QUERY_LENGTH)],
    service: SeriesServiceDep,
) -> list[SeriesOut]:
    """Search series by name."""
    results = await service.search(q)
    return [SeriesOut.from_domain(s) for s in results]


@router.get("/{series_id}", response_model=SeriesDetailOut)
async def get_series_detail(
    series_id: int,
    service: SeriesServiceDep,
) -> SeriesDetailOut:
    """Return a series with seasons, episodes and watched state."""
    detail = await service.get_details(series_id)
    return SeriesDetailOut.from_domain(detail)
