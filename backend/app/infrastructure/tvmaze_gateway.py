"""TVMaze adapter implementing the SeriesCatalog protocol."""

import html
import re
import time
from typing import Any

import httpx

from app.domain.errors import NotFoundError, UpstreamError
from app.domain.models import Episode, Series

TVMAZE_BASE_URL = "https://api.tvmaze.com"
TVMAZE_TIMEOUT_SECONDS = 5.0
SEARCH_CACHE_TTL = 300.0  # 5 min — search results may change
DETAIL_CACHE_TTL = 21600.0  # 6 hours — show/episode metadata is stable
HTTP_NOT_FOUND = 404

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def strip_html(raw: str | None) -> str | None:
    """Remove HTML tags and collapse whitespace from a TVMaze summary."""
    if raw is None:
        return None
    text = html.unescape(_TAG_RE.sub(" ", raw))
    cleaned = _WS_RE.sub(" ", text).strip()
    return cleaned or None


def _image_url(payload: dict[str, Any]) -> str | None:
    image = payload.get("image") or {}
    return image.get("original") or image.get("medium")


def map_series(payload: dict[str, Any]) -> Series:
    """Convert a raw TVMaze show payload into a domain Series."""
    rating = (payload.get("rating") or {}).get("average")
    return Series(
        id=payload["id"],
        name=payload["name"],
        summary=strip_html(payload.get("summary")),
        genres=tuple(payload.get("genres") or ()),
        premiered=payload.get("premiered"),
        status=payload.get("status"),
        image_url=_image_url(payload),
        rating=float(rating) if rating is not None else None,
    )


def map_episode(payload: dict[str, Any], series_id: int) -> Episode:
    """Convert a raw TVMaze episode payload into a domain Episode."""
    return Episode(
        id=payload["id"],
        series_id=series_id,
        season=payload.get("season") or 0,
        number=payload.get("number"),
        name=payload.get("name") or f"Episode {payload.get('number')}",
        summary=strip_html(payload.get("summary")),
        airdate=payload.get("airdate") or None,
        image_url=_image_url(payload),
        runtime=payload.get("runtime"),
    )


class TTLCache:
    """Minimal in-memory cache with per-entry expiry."""

    def __init__(self, ttl_seconds: float = DETAIL_CACHE_TTL) -> None:
        """Create a cache whose entries live for ``ttl_seconds``."""
        self._ttl = ttl_seconds
        self._entries: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        """Return the cached value or None when missing/expired."""
        entry = self._entries.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() >= expires_at:
            del self._entries[key]
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        """Store a value under ``key``."""
        self._entries[key] = (time.monotonic() + self._ttl, value)


class TVMazeGateway:
    """HTTP client for the TVMaze public API with a TTL cache."""

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        base_url: str = TVMAZE_BASE_URL,
        search_cache: TTLCache | None = None,
        detail_cache: TTLCache | None = None,
    ) -> None:
        """Create the gateway, optionally injecting a client for tests."""
        self._client = client or httpx.AsyncClient(
            base_url=base_url,
            timeout=TVMAZE_TIMEOUT_SECONDS,
        )
        self._search_cache = search_cache or TTLCache(
            ttl_seconds=SEARCH_CACHE_TTL,
        )
        self._detail_cache = detail_cache or TTLCache(
            ttl_seconds=DETAIL_CACHE_TTL,
        )

    async def aclose(self) -> None:
        """Release the underlying HTTP client."""
        await self._client.aclose()

    async def _get_json(
        self,
        path: str,
        params: dict[str, str],
        cache: TTLCache,
    ) -> Any:
        key = f"{path}?{sorted(params.items())}"
        cached = cache.get(key)
        if cached is not None:
            return cached
        try:
            response = await self._client.get(path, params=params)
        except httpx.HTTPError as e:
            raise UpstreamError("TVMaze unavailable") from e
        if response.status_code == HTTP_NOT_FOUND:
            raise NotFoundError(f"Resource {path} not found")
        if response.is_error:
            raise UpstreamError(
                f"TVMaze responded with {response.status_code}",
            )
        data = response.json()
        cache.set(key, data)
        return data

    async def search(self, query: str) -> list[Series]:
        """Search shows by name (cached 5 min)."""
        data = await self._get_json(
            "/search/shows",
            {"q": query},
            cache=self._search_cache,
        )
        return [map_series(item["show"]) for item in data]

    async def get_series(self, series_id: int) -> Series:
        """Fetch a single show by id (cached 6h)."""
        try:
            data = await self._get_json(
                f"/shows/{series_id}",
                {},
                cache=self._detail_cache,
            )
        except NotFoundError as e:
            raise NotFoundError(f"Series {series_id} not found") from e
        return map_series(data)

    async def get_episodes(self, series_id: int) -> list[Episode]:
        """Fetch all episodes of a show (cached 6h)."""
        try:
            data = await self._get_json(
                f"/shows/{series_id}/episodes",
                {},
                cache=self._detail_cache,
            )
        except NotFoundError as e:
            raise NotFoundError(f"Series {series_id} not found") from e
        return [map_episode(item, series_id) for item in data]
