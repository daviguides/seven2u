"""Immutable Pydantic domain models."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

InsightSource = Literal["llm:groq", "heuristic:fallback"]

SPECIALS_SEASON = 0


class FrozenModel(BaseModel):
    """Base for all immutable domain models."""

    model_config = ConfigDict(frozen=True)


class Series(FrozenModel):
    """A TV series as exposed by the catalogue."""

    id: int
    name: str
    summary: str | None = None
    genres: tuple[str, ...] = ()
    premiered: str | None = None
    status: str | None = None
    image_url: str | None = None
    rating: float | None = None


class Episode(FrozenModel):
    """A single episode of a series."""

    id: int
    series_id: int
    season: int
    number: int | None
    name: str
    summary: str | None = None
    airdate: str | None = None
    image_url: str | None = None
    runtime: int | None = None


class Season(FrozenModel):
    """Episodes of one season together with watched state."""

    number: int
    episodes: tuple[Episode, ...]
    watched_ids: frozenset[int] = frozenset()

    @property
    def watched_count(self) -> int:
        """Number of episodes in this season marked as watched."""
        return sum(1 for ep in self.episodes if ep.id in self.watched_ids)

    @property
    def completion(self) -> float:
        """Ratio of watched episodes, between 0.0 and 1.0."""
        if not self.episodes:
            return 0.0
        return self.watched_count / len(self.episodes)


class SeriesDetail(FrozenModel):
    """Series plus its seasons hydrated with watched state."""

    series: Series
    seasons: tuple[Season, ...]

    @property
    def total_episodes(self) -> int:
        """Total number of episodes across all seasons."""
        return sum(len(s.episodes) for s in self.seasons)

    @property
    def watched_count(self) -> int:
        """Total watched episodes across all seasons."""
        return sum(s.watched_count for s in self.seasons)


class WatchedEpisode(FrozenModel):
    """Persisted watched marker for an episode."""

    episode_id: int
    series_id: int
    watched_at: datetime


class Comment(FrozenModel):
    """User comment on a series or one of its episodes."""

    id: uuid.UUID
    series_id: int
    episode_id: int | None
    content: str
    created_at: datetime


class InsightContext(FrozenModel):
    """Everything a provider needs to write a spoiler-free insight."""

    series: Series
    episode: Episode | None = None
    total_episodes: int = 0
    watched_count: int = 0
    comments: tuple[str, ...] = ()


class SeriesInsight(FrozenModel):
    """AI (or heuristic) generated insight."""

    text: str
    highlights: tuple[str, ...] = ()
    source: InsightSource
