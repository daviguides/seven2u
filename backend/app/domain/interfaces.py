"""Protocols that services depend on; infrastructure implements them."""

from typing import Protocol

from app.domain.models import (
    Comment,
    Episode,
    InsightContext,
    Series,
    SeriesInsight,
    WatchedEpisode,
)


class SeriesCatalog(Protocol):
    """Read-only access to the external series catalogue."""

    async def search(self, query: str) -> list[Series]:
        """Search series by free text."""
        ...

    async def get_series(self, series_id: int) -> Series:
        """Fetch one series; raise NotFoundError if missing."""
        ...

    async def get_episodes(self, series_id: int) -> list[Episode]:
        """Fetch all episodes of a series."""
        ...


class WatchedRepository(Protocol):
    """Persistence for watched episode markers."""

    async def ids_for_series(self, series_id: int) -> frozenset[int]:
        """Return watched episode ids for a series."""
        ...

    async def set_watched(
        self,
        *,
        series_id: int,
        episode_id: int,
        watched: bool,
    ) -> WatchedEpisode | None:
        """Idempotently set watched state; return the marker when set."""
        ...


class CommentRepository(Protocol):
    """Persistence for user comments."""

    async def add(
        self,
        *,
        series_id: int,
        episode_id: int | None,
        content: str,
    ) -> Comment:
        """Persist a new comment."""
        ...

    async def list_for(
        self,
        *,
        series_id: int,
        episode_id: int | None,
    ) -> list[Comment]:
        """List comments for a series (episode_id None) or an episode."""
        ...

    async def list_for_series_all(self, series_id: int) -> list[Comment]:
        """List every comment attached to a series or its episodes."""
        ...


class InsightProvider(Protocol):
    """Generates a spoiler-free insight from a context."""

    async def generate_insight(self, context: InsightContext) -> SeriesInsight:
        """Produce an insight; may raise on failure."""
        ...
