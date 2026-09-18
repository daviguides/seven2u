"""Search and series detail use cases."""

import asyncio

from app.domain.errors import ValidationError
from app.domain.interfaces import SeriesCatalog, WatchedRepository
from app.domain.models import Series, SeriesDetail
from app.domain.progress import group_by_season

MAX_QUERY_LENGTH = 100


class SeriesService:
    """Reads series from the catalogue and joins user watched state."""

    def __init__(
        self,
        *,
        catalog: SeriesCatalog,
        watched_repo: WatchedRepository,
    ) -> None:
        """Inject the catalogue and watched repository."""
        self._catalog = catalog
        self._watched = watched_repo

    async def search(self, query: str) -> list[Series]:
        """Search series by name.

        Raises:
            ValidationError: When the query is blank or too long.
        """
        cleaned = query.strip()
        if not cleaned:
            raise ValidationError("Search query must not be empty")
        if len(cleaned) > MAX_QUERY_LENGTH:
            raise ValidationError(
                f"Search query must be at most {MAX_QUERY_LENGTH} characters",
            )
        return await self._catalog.search(cleaned)

    async def get_details(self, series_id: int) -> SeriesDetail:
        """Return the series with seasons and watched state hydrated."""
        series, episodes, watched_ids = await asyncio.gather(
            self._catalog.get_series(series_id),
            self._catalog.get_episodes(series_id),
            self._watched.ids_for_series(series_id),
        )
        seasons = group_by_season(episodes, watched_ids)
        return SeriesDetail(series=series, seasons=seasons)
