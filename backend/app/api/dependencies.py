"""FastAPI dependency wiring for services and repositories."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.domain.interfaces import (
    CommentRepository,
    InsightProvider,
    SeriesCatalog,
    WatchedRepository,
)
from app.infrastructure.comment_repo import SqlCommentRepository
from app.infrastructure.heuristic_provider import HeuristicTemplateProvider
from app.infrastructure.huggingface_provider import HuggingFaceProvider
from app.infrastructure.tvmaze_gateway import TVMazeGateway
from app.infrastructure.watched_repo import SqlWatchedRepository
from app.services.comment_service import CommentService
from app.services.insight_service import InsightService
from app.services.series_service import SeriesService
from app.services.tracking_service import TrackingService


def get_settings_dep(request: Request) -> Settings:
    """Return the settings attached to the app."""
    return request.app.state.settings


def get_catalog(request: Request) -> SeriesCatalog:
    """Return the process-wide TVMaze gateway (created lazily)."""
    catalog = getattr(request.app.state, "catalog", None)
    if catalog is None:
        catalog = TVMazeGateway()
        request.app.state.catalog = catalog
    return catalog


def get_llm_provider(request: Request) -> InsightProvider | None:
    """Return the HuggingFace provider, or None when no key is set."""
    settings: Settings = request.app.state.settings
    if not settings.huggingface_api_key:
        return None
    provider = getattr(request.app.state, "llm_provider", None)
    if provider is None:
        provider = HuggingFaceProvider(
            api_key=settings.huggingface_api_key,
            model=settings.huggingface_model,
        )
        request.app.state.llm_provider = provider
    return provider


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield one database session per request."""
    async with request.app.state.session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
CatalogDep = Annotated[SeriesCatalog, Depends(get_catalog)]
LlmProviderDep = Annotated[InsightProvider | None, Depends(get_llm_provider)]


def get_watched_repo(session: SessionDep) -> WatchedRepository:
    """Build the SQL watched repository."""
    return SqlWatchedRepository(session)


def get_comment_repo(session: SessionDep) -> CommentRepository:
    """Build the SQL comment repository."""
    return SqlCommentRepository(session)


WatchedRepoDep = Annotated[WatchedRepository, Depends(get_watched_repo)]
CommentRepoDep = Annotated[CommentRepository, Depends(get_comment_repo)]


def get_series_service(
    catalog: CatalogDep,
    watched_repo: WatchedRepoDep,
) -> SeriesService:
    """Build the series service."""
    return SeriesService(catalog=catalog, watched_repo=watched_repo)


def get_tracking_service(
    catalog: CatalogDep,
    watched_repo: WatchedRepoDep,
) -> TrackingService:
    """Build the tracking service."""
    return TrackingService(catalog=catalog, watched_repo=watched_repo)


def get_comment_service(comment_repo: CommentRepoDep) -> CommentService:
    """Build the comment service."""
    return CommentService(comment_repo=comment_repo)


def get_insight_service(
    catalog: CatalogDep,
    watched_repo: WatchedRepoDep,
    comment_repo: CommentRepoDep,
    llm_provider: LlmProviderDep,
) -> InsightService:
    """Build the insight service with LLM primary and heuristic fallback."""
    return InsightService(
        catalog=catalog,
        watched_repo=watched_repo,
        comment_repo=comment_repo,
        primary=llm_provider,
        fallback=HeuristicTemplateProvider(),
    )
