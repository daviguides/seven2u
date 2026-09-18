"""End-to-end API tests against an in-memory SQLite database.

The TVMaze catalogue and the LLM provider are replaced through FastAPI
dependency overrides; the SQL repositories run for real.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_catalog, get_llm_provider
from app.config import Settings
from app.infrastructure.database import create_async_engine, init_db
from app.main import create_app
from tests.fakes import FakeCatalog, StubProvider, make_episode, make_series

SERIES_ID = 1


@pytest.fixture
def stub_provider():
    return StubProvider(text="llm says hi")


@pytest.fixture
async def client(stub_provider):
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    await init_db(engine)

    series = make_series(SERIES_ID)
    catalog = FakeCatalog(
        series=[series],
        episodes={SERIES_ID: [make_episode(11, 1, 1), make_episode(12, 1, 2)]},
    )
    app = create_app(Settings(static_dir="/nonexistent"))
    app.state.engine = engine
    app.state.session_factory = async_sessionmaker(
        engine, expire_on_commit=False
    )
    app.dependency_overrides[get_catalog] = lambda: catalog
    app.dependency_overrides[get_llm_provider] = lambda: stub_provider

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://t") as c:
        yield c
    await engine.dispose()


async def test_health(client):
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_search_returns_series(client):
    response = await client.get("/api/v1/series/search", params={"q": "bad"})

    assert response.status_code == 200
    assert response.json()[0]["name"] == "Breaking Bad"


async def test_search_rejects_empty_query(client):
    response = await client.get("/api/v1/series/search", params={"q": ""})

    assert response.status_code == 422


async def test_unknown_series_returns_404(client):
    response = await client.get("/api/v1/series/999")

    assert response.status_code == 404
    assert "999" in response.json()["detail"]


async def test_watched_toggle_is_idempotent_and_reflected_in_detail(client):
    body = {"series_id": SERIES_ID, "watched": True}

    first = await client.put("/api/v1/episodes/11/watched", json=body)
    second = await client.put("/api/v1/episodes/11/watched", json=body)
    detail = await client.get(f"/api/v1/series/{SERIES_ID}")

    assert first.status_code == 200
    assert first.json()["watched"] is True
    assert first.json()["watched_at"] == second.json()["watched_at"]
    season = detail.json()["seasons"][0]
    assert season["watched_count"] == 1
    assert season["completion"] == 0.5
    assert [e["watched"] for e in season["episodes"]] == [True, False]


async def test_unwatch_clears_state(client):
    await client.put(
        "/api/v1/episodes/11/watched",
        json={"series_id": SERIES_ID, "watched": True},
    )

    response = await client.put(
        "/api/v1/episodes/11/watched",
        json={"series_id": SERIES_ID, "watched": False},
    )
    detail = await client.get(f"/api/v1/series/{SERIES_ID}")

    assert response.json()["watched"] is False
    assert detail.json()["watched_count"] == 0


async def test_watched_episode_outside_series_returns_404(client):
    response = await client.put(
        "/api/v1/episodes/999/watched",
        json={"series_id": SERIES_ID, "watched": True},
    )

    assert response.status_code == 404


async def test_comments_series_and_episode_are_separate(client):
    base = f"/api/v1/series/{SERIES_ID}/comments"

    created = await client.post(base, json={"content": "  series note "})
    await client.post(f"{base}?episode_id=11", json={"content": "ep note"})
    series_list = await client.get(base)
    episode_list = await client.get(f"{base}?episode_id=11")

    assert created.status_code == 201
    assert created.json()["content"] == "series note"
    assert [c["content"] for c in series_list.json()] == ["series note"]
    assert [c["content"] for c in episode_list.json()] == ["ep note"]


async def test_blank_comment_rejected(client):
    response = await client.post(
        f"/api/v1/series/{SERIES_ID}/comments",
        json={"content": "   "},
    )

    assert response.status_code == 422


async def test_insight_uses_llm_when_available(client):
    response = await client.get(f"/api/v1/series/{SERIES_ID}/insights")

    assert response.status_code == 200
    assert response.json()["source"] == "llm:groq"
    assert response.json()["text"] == "llm says hi"


async def test_insight_falls_back_when_provider_fails(client, stub_provider):
    stub_provider.error = RuntimeError("down")

    response = await client.get(
        f"/api/v1/series/{SERIES_ID}/insights/episodes/11"
    )

    assert response.status_code == 200
    assert response.json()["source"] == "heuristic:fallback"
    assert "S1E1" in response.json()["text"]
