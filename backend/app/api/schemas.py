"""Request and response DTOs for the HTTP API."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.models import (
    Comment,
    Episode,
    InsightSource,
    Season,
    Series,
    SeriesDetail,
    SeriesInsight,
)

MAX_COMMENT_LENGTH = 2000


class SeriesOut(BaseModel):
    """Public representation of a series."""

    id: int
    name: str
    summary: str | None
    genres: list[str]
    premiered: str | None
    status: str | None
    image_url: str | None
    rating: float | None

    @classmethod
    def from_domain(cls, series: Series) -> "SeriesOut":
        """Map a domain Series to its DTO."""
        return cls(
            id=series.id,
            name=series.name,
            summary=series.summary,
            genres=list(series.genres),
            premiered=series.premiered,
            status=series.status,
            image_url=series.image_url,
            rating=series.rating,
        )


class EpisodeOut(BaseModel):
    """Episode with its watched flag."""

    id: int
    season: int
    number: int | None
    name: str
    summary: str | None
    airdate: str | None
    image_url: str | None
    runtime: int | None
    watched: bool

    @classmethod
    def from_domain(cls, episode: Episode, watched: bool) -> "EpisodeOut":
        """Map a domain Episode plus watched flag to its DTO."""
        return cls(
            id=episode.id,
            season=episode.season,
            number=episode.number,
            name=episode.name,
            summary=episode.summary,
            airdate=episode.airdate,
            image_url=episode.image_url,
            runtime=episode.runtime,
            watched=watched,
        )


class SeasonOut(BaseModel):
    """Season with episodes and completion progress."""

    number: int
    episodes: list[EpisodeOut]
    watched_count: int
    total: int
    completion: float

    @classmethod
    def from_domain(cls, season: Season) -> "SeasonOut":
        """Map a domain Season to its DTO."""
        return cls(
            number=season.number,
            episodes=[
                EpisodeOut.from_domain(ep, ep.id in season.watched_ids)
                for ep in season.episodes
            ],
            watched_count=season.watched_count,
            total=len(season.episodes),
            completion=season.completion,
        )


class SeriesDetailOut(BaseModel):
    """Series with seasons and overall progress."""

    series: SeriesOut
    seasons: list[SeasonOut]
    total_episodes: int
    watched_count: int

    @classmethod
    def from_domain(cls, detail: SeriesDetail) -> "SeriesDetailOut":
        """Map a domain SeriesDetail to its DTO."""
        return cls(
            series=SeriesOut.from_domain(detail.series),
            seasons=[SeasonOut.from_domain(s) for s in detail.seasons],
            total_episodes=detail.total_episodes,
            watched_count=detail.watched_count,
        )


class WatchedIn(BaseModel):
    """Body for the idempotent watched toggle."""

    series_id: int = Field(ge=1)
    watched: bool


class WatchedOut(BaseModel):
    """Result of a watched toggle."""

    episode_id: int
    series_id: int
    watched: bool
    watched_at: datetime | None


class CommentIn(BaseModel):
    """Body for creating a comment."""

    content: str = Field(min_length=1, max_length=MAX_COMMENT_LENGTH)


class CommentOut(BaseModel):
    """Public representation of a comment."""

    id: uuid.UUID
    series_id: int
    episode_id: int | None
    content: str
    created_at: datetime

    @classmethod
    def from_domain(cls, comment: Comment) -> "CommentOut":
        """Map a domain Comment to its DTO."""
        return cls(
            id=comment.id,
            series_id=comment.series_id,
            episode_id=comment.episode_id,
            content=comment.content,
            created_at=comment.created_at,
        )


class InsightOut(BaseModel):
    """AI or heuristic insight."""

    text: str
    highlights: list[str]
    source: InsightSource

    @classmethod
    def from_domain(cls, insight: SeriesInsight) -> "InsightOut":
        """Map a domain SeriesInsight to its DTO."""
        return cls(
            text=insight.text,
            highlights=list(insight.highlights),
            source=insight.source,
        )
