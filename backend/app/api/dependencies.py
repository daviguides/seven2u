"""FastAPI dependency wiring for services and repositories."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces import SeriesCatalog, WatchedRepository
from app.infrastructure.tvmaze_gateway import TVMazeGateway
from app.infrastructure.watched_repo import SqlWatchedRepository
from app.services.series_service import SeriesService


def get_catalog(request: Request) -> SeriesCatalog:
    """Return the process-wide TVMaze gateway (created lazily)."""
    catalog = getattr(request.app.state, "catalog", None)
    if catalog is None:
        catalog = TVMazeGateway()
        request.app.state.catalog = catalog
    return catalog


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield one database session per request."""
    async with request.app.state.session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
CatalogDep = Annotated[SeriesCatalog, Depends(get_catalog)]


def get_watched_repo(session: SessionDep) -> WatchedRepository:
    """Build the SQL watched repository."""
    return SqlWatchedRepository(session)


WatchedRepoDep = Annotated[WatchedRepository, Depends(get_watched_repo)]


def get_series_service(
    catalog: CatalogDep,
    watched_repo: WatchedRepoDep,
) -> SeriesService:
    """Build the series service."""
    return SeriesService(catalog=catalog, watched_repo=watched_repo)
