"""In-memory fakes satisfying the domain protocols."""

import uuid
from datetime import UTC, datetime

from app.domain.errors import NotFoundError
from app.domain.models import (
    Comment,
    Episode,
    InsightContext,
    Series,
    SeriesInsight,
    WatchedEpisode,
)


def make_series(series_id: int = 1, **overrides: object) -> Series:
    base: dict[str, object] = {
        "id": series_id,
        "name": "Breaking Bad",
        "summary": "A chemistry teacher turns to crime.",
        "genres": ("Drama", "Crime", "Thriller"),
        "premiered": "2008-01-20",
        "status": "Ended",
        "image_url": "https://img/bb.jpg",
        "rating": 9.2,
    }
    base.update(overrides)
    return Series.model_validate(base)


def make_episode(
    episode_id: int,
    season: int,
    number: int | None,
    series_id: int = 1,
) -> Episode:
    return Episode(
        id=episode_id,
        series_id=series_id,
        season=season,
        number=number,
        name=f"S{season}E{number}",
        summary="Something happens.",
        airdate="2008-01-20",
    )


class FakeCatalog:
    def __init__(
        self,
        series: list[Series] | None = None,
        episodes: dict[int, list[Episode]] | None = None,
    ) -> None:
        self.series = {s.id: s for s in (series or [])}
        self.episodes = episodes or {}
        self.search_calls: list[str] = []

    async def search(self, query: str) -> list[Series]:
        self.search_calls.append(query)
        return [
            s for s in self.series.values() if query.lower() in s.name.lower()
        ]

    async def get_series(self, series_id: int) -> Series:
        if series_id not in self.series:
            raise NotFoundError(f"Series {series_id} not found")
        return self.series[series_id]

    async def get_episodes(self, series_id: int) -> list[Episode]:
        if series_id not in self.series:
            raise NotFoundError(f"Series {series_id} not found")
        return list(self.episodes.get(series_id, []))


class FakeWatchedRepository:
    def __init__(self) -> None:
        self.rows: dict[int, WatchedEpisode] = {}

    async def ids_for_series(self, series_id: int) -> frozenset[int]:
        return frozenset(
            ep_id
            for ep_id, row in self.rows.items()
            if row.series_id == series_id
        )

    async def set_watched(
        self,
        *,
        series_id: int,
        episode_id: int,
        watched: bool,
    ) -> WatchedEpisode | None:
        if not watched:
            self.rows.pop(episode_id, None)
            return None
        if episode_id not in self.rows:
            self.rows[episode_id] = WatchedEpisode(
                episode_id=episode_id,
                series_id=series_id,
                watched_at=datetime.now(UTC),
            )
        return self.rows[episode_id]


class FakeCommentRepository:
    def __init__(self) -> None:
        self.rows: list[Comment] = []

    async def add(
        self,
        *,
        series_id: int,
        episode_id: int | None,
        content: str,
    ) -> Comment:
        comment = Comment(
            id=uuid.uuid4(),
            series_id=series_id,
            episode_id=episode_id,
            content=content,
            created_at=datetime.now(UTC),
        )
        self.rows.append(comment)
        return comment

    async def list_for(
        self,
        *,
        series_id: int,
        episode_id: int | None,
    ) -> list[Comment]:
        return [
            c
            for c in self.rows
            if c.series_id == series_id and c.episode_id == episode_id
        ]

    async def list_for_series_all(self, series_id: int) -> list[Comment]:
        return [c for c in self.rows if c.series_id == series_id]


class StubProvider:
    def __init__(
        self,
        text: str = "stub insight",
        error: Exception | None = None,
    ) -> None:
        self.text = text
        self.error = error
        self.calls: list[InsightContext] = []

    async def generate_insight(self, context: InsightContext) -> SeriesInsight:
        self.calls.append(context)
        if self.error is not None:
            raise self.error
        return SeriesInsight(text=self.text, source="llm:huggingface")
