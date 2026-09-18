"""Async SQLAlchemy engine, session factory and startup helpers."""

import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.infrastructure.db_models import Base

DB_MAX_RETRIES = 10
DB_RETRY_DELAY_SECONDS = 1.5

logger = logging.getLogger(__name__)


def create_engine(database_url: str) -> AsyncEngine:
    """Build an async engine for the given connection string."""
    return create_async_engine(database_url, pool_pre_ping=True)


def create_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Build a session factory bound to the engine."""
    return async_sessionmaker(engine, expire_on_commit=False)


async def wait_for_database(
    engine: AsyncEngine,
    max_retries: int = DB_MAX_RETRIES,
    delay: float = DB_RETRY_DELAY_SECONDS,
) -> None:
    """Block until the database accepts connections.

    Docker Compose `depends_on` does not wait for Postgres readiness, so
    the app retries a trivial query before creating tables.

    Raises:
        Exception: The last connection error once retries are exhausted.
    """
    for attempt in range(1, max_retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return
        except Exception:
            if attempt == max_retries:
                raise
            logger.warning(
                "Database not ready (attempt %d/%d), retrying",
                attempt,
                max_retries,
            )
            await asyncio.sleep(delay)


async def init_db(engine: AsyncEngine) -> None:
    """Create all tables if they do not exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
