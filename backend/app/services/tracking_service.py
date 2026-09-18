"""Watched-episode tracking use cases."""

from app.domain.errors import NotFoundError
from app.domain.interfaces import SeriesCatalog, WatchedRepository
from app.domain.models import Episode, WatchedEpisode


class TrackingService:
    """Marks episodes as watched after validating they exist."""

    def __init__(
        self,
        *,
        catalog: SeriesCatalog,
        watched_repo: WatchedRepository,
    ) -> None:
        """Inject the catalogue and watched repository."""
        self._catalog = catalog
        self._watched = watched_repo

    async def find_episode(
        self,
        *,
        series_id: int,
        episode_id: int,
    ) -> Episode:
        """Return the episode or raise if it is not part of the series."""
        episodes = await self._catalog.get_episodes(series_id)
        for episode in episodes:
            if episode.id == episode_id:
                return episode
        raise NotFoundError(
            f"Episode {episode_id} not found in series {series_id}",
        )

    async def set_watched(
        self,
        *,
        series_id: int,
        episode_id: int,
        watched: bool,
    ) -> WatchedEpisode | None:
        """Idempotently set the watched state of an episode."""
        await self.find_episode(series_id=series_id, episode_id=episode_id)
        return await self._watched.set_watched(
            series_id=series_id,
            episode_id=episode_id,
            watched=watched,
        )

    async def watched_ids(self, series_id: int) -> frozenset[int]:
        """Return all watched episode ids for a series."""
        return await self._watched.ids_for_series(series_id)
