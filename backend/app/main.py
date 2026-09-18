"""FastAPI application factory: lifespan, API router and SPA mount."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.config import Settings, get_settings
from app.infrastructure.database import (
    create_engine,
    create_session_factory,
    init_db,
    wait_for_database,
)

API_PREFIX = "/api/v1"
INDEX_FILE = "index.html"

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Open the database on startup and dispose it on shutdown."""
    settings: Settings = app.state.settings
    engine = create_engine(settings.database_url)
    await wait_for_database(engine)
    await init_db(engine)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    logger.info("Database ready")
    yield
    await engine.dispose()


def _mount_spa(app: FastAPI, static_dir: Path) -> None:
    """Serve the compiled React SPA with a catch-all for client routes."""
    assets_dir = static_dir / "assets"
    if assets_dir.is_dir():
        app.mount(
            "/assets",
            StaticFiles(directory=assets_dir),
            name="assets",
        )
    index_path = static_dir / INDEX_FILE

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> FileResponse:
        candidate = static_dir / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index_path)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI application.

    Args:
        settings: Optional settings override, mainly for tests.

    Returns:
        A configured FastAPI instance.
    """
    settings = settings or get_settings()
    app = FastAPI(title="Seven2U", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.include_router(api_router, prefix=API_PREFIX)

    static_dir = Path(settings.static_dir)
    if (static_dir / INDEX_FILE).is_file():
        _mount_spa(app, static_dir)
    return app


app = create_app()
