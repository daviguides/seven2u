"""SQLAlchemy implementation of WatchedRepository."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import WatchedEpisode
from app.infrastructure.db_models import WatchedEpisodeRow


class SqlWatchedRepository:
    """Stores watched markers in the ``watched_episodes`` table."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the repository to a request-scoped session."""
        self._session = session

    async def ids_for_series(self, series_id: int) -> frozenset[int]:
        """Return all watched episode ids for a series."""
        stmt = select(WatchedEpisodeRow.episode_id).where(
            WatchedEpisodeRow.series_id == series_id,
        )
        result = await self._session.execute(stmt)
        return frozenset(result.scalars().all())

    async def set_watched(
        self,
        *,
        series_id: int,
        episode_id: int,
        watched: bool,
    ) -> WatchedEpisode | None:
        """Insert or delete the marker so the end state matches ``watched``."""
        if not watched:
            await self._session.execute(
                delete(WatchedEpisodeRow).where(
                    WatchedEpisodeRow.episode_id == episode_id,
                ),
            )
            await self._session.commit()
            return None

        row = await self._session.get(WatchedEpisodeRow, episode_id)
        if row is None:
            row = WatchedEpisodeRow(episode_id=episode_id, series_id=series_id)
            self._session.add(row)
            await self._session.commit()
            await self._session.refresh(row)
        return WatchedEpisode(
            episode_id=row.episode_id,
            series_id=row.series_id,
            watched_at=row.watched_at,
        )
