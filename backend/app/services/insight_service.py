"""Insight use case: try the LLM provider, fall back to heuristics."""

import asyncio
import logging
import time

from app.domain.errors import NotFoundError
from app.domain.interfaces import (
    CommentRepository,
    InsightProvider,
    SeriesCatalog,
    WatchedRepository,
)
from app.domain.models import InsightContext, SeriesInsight

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 86400  # 24 hours

_insight_cache: dict[str, tuple[float, SeriesInsight]] = {}


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
        self._cache = _insight_cache

    async def _build_context(
        self,
        *,
        series_id: int,
        episode_id: int | None,
    ) -> InsightContext:
        series, episodes = await asyncio.gather(
            self._catalog.get_series(series_id),
            self._catalog.get_episodes(series_id),
        )
        # Both repositories share one session; sessions are not
        # concurrency-safe, so these two reads stay sequential.
        watched_ids = await self._watched.ids_for_series(series_id)
        comments = await self._comments.list_for_series_all(series_id)
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

    def _cache_key(
        self,
        series_id: int,
        episode_id: int | None,
    ) -> str:
        return f"{series_id}:{episode_id or 'series'}"

    def _get_cached(self, key: str) -> SeriesInsight | None:
        entry = self._cache.get(key)
        if entry is None:
            return None
        ts, insight = entry
        if time.monotonic() - ts > CACHE_TTL_SECONDS:
            del self._cache[key]
            return None
        return insight

    async def _generate(self, context: InsightContext) -> SeriesInsight:
        if self._primary is None:
            return await self._fallback.generate_insight(context)
        try:
            return await self._primary.generate_insight(context)
        except Exception as e:  # noqa: BLE001 - any provider failure falls back
            logger.warning("Primary insight provider failed: %s", e)
            return await self._fallback.generate_insight(context)

    async def for_series(self, series_id: int) -> SeriesInsight:
        """Generate an insight for a whole series (cached 24h)."""
        key = self._cache_key(series_id, None)
        cached = self._get_cached(key)
        if cached is not None:
            return cached
        context = await self._build_context(
            series_id=series_id,
            episode_id=None,
        )
        result = await self._generate(context)
        self._cache[key] = (time.monotonic(), result)
        return result

    async def for_episode(
        self,
        *,
        series_id: int,
        episode_id: int,
    ) -> SeriesInsight:
        """Generate an insight for one episode (cached 24h)."""
        key = self._cache_key(series_id, episode_id)
        cached = self._get_cached(key)
        if cached is not None:
            return cached
        context = await self._build_context(
            series_id=series_id,
            episode_id=episode_id,
        )
        result = await self._generate(context)
        self._cache[key] = (time.monotonic(), result)
        return result
