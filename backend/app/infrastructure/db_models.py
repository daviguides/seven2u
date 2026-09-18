"""SQLAlchemy ORM models for user-generated data."""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base shared by all tables."""


class WatchedEpisodeRow(Base):
    """Persisted watched state for a single episode."""

    __tablename__ = "watched_episodes"

    episode_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    series_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    watched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
    )


class CommentRow(Base):
    """User comment attached to a series or a single episode."""

    __tablename__ = "comments"
    __table_args__ = (
        CheckConstraint(
            "length(trim(content)) > 0",
            name="ck_comments_content_not_blank",
        ),
        Index("idx_comments_target", "series_id", "episode_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    series_id: Mapped[int] = mapped_column(Integer, nullable=False)
    episode_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
    )
