"""Insight use case: try the LLM provider, fall back to heuristics."""

import asyncio
import logging

from app.domain.errors import NotFoundError
from app.domain.interfaces import (
    CommentRepository,
    InsightProvider,
    SeriesCatalog,
    WatchedRepository,
)
from app.domain.models import InsightContext, SeriesInsight

logger = logging.getLogger(__name__)


class InsightService:
    """Builds the insight context and orchestrates providers."""

    def __init__(
        self,
        *,
        catalog: SeriesCatalog,
        watched_repo: WatchedRepository,
        comment_repo: CommentRepository,
        primary: InsightProvider | None,
        fallback: InsightProvider,
    ) -> None:
        """Inject data sources plus optional primary and fallback providers."""
        self._catalog = catalog
        self._watched = watched_repo
        self._comments = comment_repo
        self._primary = primary
        self._fallback = fallback

    async def _build_context(
        self,
        *,
        series_id: int,
        episode_id: int | None,
    ) -> InsightContext:
        series, episodes, watched_ids, comments = await asyncio.gather(
            self._catalog.get_series(series_id),
            self._catalog.get_episodes(series_id),
            self._watched.ids_for_series(series_id),
            self._comments.list_for_series_all(series_id),
        )
        episode = None
        if episode_id is not None:
            episode = next((e for e in episodes if e.id == episode_id), None)
            if episode is None:
                raise NotFoundError(
                    f"Episode {episode_id} not found in series {series_id}",
                )
            comments = [c for c in comments if c.episode_id == episode_id]
        return InsightContext(
            series=series,
            episode=episode,
            total_episodes=len(episodes),
            watched_count=len(watched_ids),
            comments=tuple(c.content for c in comments),
        )

    async def _generate(self, context: InsightContext) -> SeriesInsight:
        if self._primary is None:
            return await self._fallback.generate_insight(context)
        try:
            return await self._primary.generate_insight(context)
        except Exception as e:  # noqa: BLE001 - any provider failure falls back
            logger.warning("Primary insight provider failed: %s", e)
            return await self._fallback.generate_insight(context)

    async def for_series(self, series_id: int) -> SeriesInsight:
        """Generate an insight for a whole series."""
        context = await self._build_context(
            series_id=series_id,
            episode_id=None,
        )
        return await self._generate(context)

    async def for_episode(
        self,
        *,
        series_id: int,
        episode_id: int,
    ) -> SeriesInsight:
        """Generate an insight for one episode."""
        context = await self._build_context(
            series_id=series_id,
            episode_id=episode_id,
        )
        return await self._generate(context)
