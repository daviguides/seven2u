# Seven2U Design Specification v1.0

> Interactive TV series companion: search series via TVMaze, track watched episodes, leave comments, and receive AI-generated insights. Python Clean Architecture backend, React frontend, PostgreSQL, one `docker compose up`.

beecrowd Software Architect challenge · Ready for implementation

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Backend Structure](#3-backend-structure)
4. [API Contract](#4-api-contract)
5. [Frontend Structure](#5-frontend-structure)
6. [AI Integration](#6-ai-integration)
7. [Data Model](#7-data-model)
8. [Security](#8-security)
9. [Testing Strategy](#9-testing-strategy)
10. [Docker & Infrastructure](#10-docker--infrastructure)
11. [Sequencing](#11-sequencing)

---

## 1. Overview

Seven2U ("Seven" = seventh art, "2U" = to you) is the series module of an early-stage streaming platform. A user searches for a series, opens its detail page, sees episodes grouped by season, marks episodes watched, leaves comments on the series or an episode, and asks for an AI insight that describes tone, themes and what to expect, without spoilers.

Series catalogue data is never stored: TVMaze is the source of truth for shows and episodes. Seven2U persists only what the user creates (watched state, comments) and joins it onto TVMaze data at read time. The AI provider sits behind a Protocol and degrades to a template-based insight when the LLM is unavailable, so the feature never breaks the page.

### Design Principles

- **Dependencies point inward.** `api → services → repositories → infrastructure`, with `domain` shared by all and depending on nothing.
- **Own only user data.** TVMaze IDs are foreign references; we never mirror the catalogue.
- **AI is a plug, not a pillar.** `InsightProvider` Protocol; HuggingFace is one implementation; a template provider is the fallback. The page renders with or without it.
- **Boring tools, sharp boundaries.** FastAPI, SQLAlchemy, httpx, Pydantic, React + Vite + Tailwind. No framework where a function will do.
- **Testable by construction.** Services take Protocols; tests inject in-memory fakes. No mocking framework needed for domain and service tests.

### Evaluation Mapping

| Criterion | Weight | Where this spec answers it |
|-----------|--------|---------------------------|
| Architecture & Design | 30% | §2 layers and dependency rule, §3 module layout, §6 provider isolation |
| Functionality & Stability | 30% | §4 contract with explicit error cases, §5 loading/error/empty states, §10 single-command startup |
| Code Quality | 20% | Ruff + type hints + Google docstrings (Shodo), small modules, one responsibility each |
| AI Integration | 10% | §6 Protocol, HuggingFace adapter, template fallback, timeout policy |
| Testability | 10% | §9 unit tests on domain + services via fakes, integration tests on API |

---

## 2. Architecture

```
FRONTEND (React + Vite + Tailwind)
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ features/    │  │ features/    │  │ features/    │  │ lib/api.ts   │
│ search       │  │ series       │  │ episode      │  │              │
└──────────────┘  └──────────────┘  └──────────────┘  └──────┬───────┘
                                                             │ HTTP
BACKEND (FastAPI, Clean Architecture)                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────┐               ┌───────────────────────────┐   │
│  │ api/routes +    │               │ infra/tvmaze              │   │
│  │ schemas         │               │ infra/ai (providers)      │   │
│  └────────┬────────┘               │ infra/db (SQLAlchemy)     │   │
│           ▼              domain    └───────────────────────────┘   │
│  ┌─────────────────┐   (shared,   ┌───────────────────────────┐   │
│  │ services        │   imports    │ config (settings)         │   │
│  └────────┬────────┘   nothing)   └───────────────────────────┘   │
│           ▼                                                       │
│  ┌─────────────────┐                                              │
│  │ repositories    │                                              │
│  │ (Protocols)     │                                              │
│  └─────────────────┘                                              │
└─────────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
  HuggingFace          api.tvmaze.com        PostgreSQL 16
  Inference
```

### Dependency Rule

| Layer | May import | Responsibility | Must not |
|-------|-----------|----------------|----------|
| `domain` | stdlib only | Entities, value objects, domain errors, pure rules (e.g. season progress) | Import FastAPI, SQLAlchemy, httpx, Pydantic |
| `repositories` | domain | Protocols describing persistence and catalogue access | Contain SQL or HTTP |
| `services` | domain, repositories | Use cases: search, detail with progress, toggle watched, add comment, generate insight | Know about HTTP status codes or request objects |
| `infrastructure` | domain, repositories | Concrete adapters: SQLAlchemy repos, TVMaze client, AI providers | Be imported by services directly (only via Protocol + DI) |
| `api` | services, domain, schemas | Routes, Pydantic schemas, dependency wiring, error mapping | Contain business rules |

### SOLID in Practice

- **S: one use case per service method** — `TrackingService.toggle_watched` does one thing. Seasons grouping lives in `domain/progress.py`, not in the route.
- **O: new AI provider = new file** — Adding Ollama or OpenAI means one class implementing `InsightProvider`. No existing code changes.
- **L: fakes are drop-ins** — `InMemoryWatchedRepository` satisfies the same Protocol as the SQLAlchemy one; services cannot tell them apart.
- **I + D: small Protocols, injected** — `ShowCatalog`, `WatchedRepository`, `CommentRepository`, `InsightProvider`. Services receive them via constructor; FastAPI `Depends` builds them.

---

## 3. Backend Structure

```
backend/
  pyproject.toml              # uv, ruff (80 cols), pytest, mypy
  app/
    main.py                   # create_app(): routers, CORS, static, lifespan
    config.py                 # Settings(BaseSettings): DATABASE_URL, HF_API_TOKEN, ...
    domain/
      models.py               # Series, Episode, Season, Comment, WatchedEpisode
      progress.py             # group_by_season(), completion_ratio()
      errors.py               # NotFoundError, UpstreamError, ValidationError
    repositories/
      protocols.py            # ShowCatalog, WatchedRepository, CommentRepository
    services/
      show_service.py         # search(), get_detail(), list_episodes()
      tracking_service.py     # toggle_watched(), watched_ids_for_show()
      comment_service.py      # add(), list_for()
      insight_service.py      # series_insight(), episode_insight()
    infrastructure/
      tvmaze/
        client.py             # httpx.AsyncClient adapter -> domain models
        mapping.py            # raw JSON -> Series / Episode
      db/
        session.py            # engine, async_sessionmaker, init_db()
        tables.py             # SQLAlchemy ORM: WatchedEpisodeRow, CommentRow
        watched_repository.py # SqlWatchedRepository
        comment_repository.py # SqlCommentRepository
      ai/
        protocol.py           # InsightProvider (Protocol), InsightRequest
        prompt.py             # build_series_prompt(), build_episode_prompt()
        huggingface.py        # HuggingFaceInsightProvider
        template.py           # TemplateInsightProvider (fallback, no network)
        resilient.py          # ResilientInsightProvider(primary, fallback, timeout)
    api/
      deps.py                 # get_session, get_show_service, get_insight_provider...
      errors.py               # domain error -> HTTP mapping
      schemas/
        shows.py  tracking.py  comments.py  insights.py
      routes/
        shows.py  tracking.py  comments.py  insights.py  health.py
  tests/
    unit/                     # domain + services, fakes only
    integration/              # httpx AsyncClient against app, real Postgres via compose
    fakes.py                  # InMemory* repositories, StubCatalog, StubProvider
```

### Domain Models

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

@dataclass(frozen=True, slots=True)
class Series:
    id: int
    name: str
    summary: str | None
    genres: tuple[str, ...]
    premiered: str | None
    image_url: str | None
    rating: float | None

@dataclass(frozen=True, slots=True)
class Episode:
    id: int
    show_id: int
    season: int
    number: int
    name: str
    summary: str | None
    airdate: str | None
    image_url: str | None

class CommentTarget(StrEnum):
    SHOW = "show"
    EPISODE = "episode"

@dataclass(frozen=True, slots=True)
class Comment:
    id: int
    target_type: CommentTarget
    target_id: int
    body: str
    created_at: datetime

@dataclass(frozen=True, slots=True)
class WatchedEpisode:
    episode_id: int
    show_id: int
    watched_at: datetime
```

Domain models are frozen dataclasses, not Pydantic. Pydantic lives at the boundaries (`api/schemas`, `config.py`).

### Repository Protocols

```python
class ShowCatalog(Protocol):
    async def search(self, query: str) -> list[Series]: ...
    async def get(self, show_id: int) -> Series: ...
    async def episodes(self, show_id: int) -> list[Episode]: ...

class WatchedRepository(Protocol):
    async def ids_for_show(self, show_id: int) -> frozenset[int]: ...
    async def mark(self, show_id: int, episode_id: int) -> WatchedEpisode: ...
    async def unmark(self, episode_id: int) -> None: ...

class CommentRepository(Protocol):
    async def add(self, target: CommentTarget, target_id: int, body: str) -> Comment: ...
    async def list_for(self, target: CommentTarget, target_id: int) -> list[Comment]: ...
```

### Services

| Service | Depends on | Methods | Notes |
|---------|-----------|---------|-------|
| `ShowService` | `ShowCatalog` | `search(q)`, `get_detail(id)` | Strips HTML from TVMaze summaries in `mapping.py`, not here |
| `TrackingService` | `ShowCatalog`, `WatchedRepository` | `episodes_with_progress(show_id)`, `set_watched(show_id, ep_id, bool)` | Verifies the episode belongs to the show before writing |
| `CommentService` | `CommentRepository` | `add(target, id, body)`, `list_for(target, id)` | Trims body; rejects empty (domain `ValidationError`) |
| `InsightService` | `ShowCatalog`, `CommentRepository`, `InsightProvider` | `for_series(id)`, `for_episode(show_id, ep_id)` | Builds `InsightRequest` from series + genres + summary + user comments |

---

## 4. API Contract

All routes prefixed `/api`. Responses JSON. Frontend static build served from `/` by the same FastAPI process, one origin on port 7777.

| Method | Path | Purpose | Response |
|--------|------|---------|----------|
| `GET` | `/api/health` | Liveness + DB reachability | `{status, db, ai_provider}` |
| `GET` | `/api/shows/search?q=` | Search TVMaze | `SeriesSummary[]` |
| `GET` | `/api/shows/{show_id}` | Series detail | `SeriesDetail` |
| `GET` | `/api/shows/{show_id}/episodes` | Episodes by season with watched state and progress | `SeasonOut[]` |
| `PUT` | `/api/shows/{show_id}/episodes/{episode_id}/watched` | Set watched state (idempotent) | `WatchedOut` |
| `GET` | `/api/comments/{target}/{target_id}` | List comments (`target` = show \| episode) | `CommentOut[]` |
| `POST` | `/api/comments/{target}/{target_id}` | Add comment | `201 CommentOut` |
| `GET` | `/api/insights/shows/{show_id}` | AI insight for series | `InsightOut` |
| `GET` | `/api/insights/shows/{show_id}/episodes/{episode_id}` | AI insight for episode | `InsightOut` |

### Error Mapping

| Domain error | HTTP | Body |
|-------------|------|------|
| `NotFoundError` | 404 | `{"detail": "Show 999 not found"}` |
| `ValidationError` | 422 | `{"detail": "..."}` |
| `UpstreamError` | 502 | `{"detail": "TVMaze unavailable"}` |
| AI provider failure | 200 | Never an error: `source: "fallback"` |

---

## 5. Frontend Structure

```
frontend/src/
  main.tsx, App.tsx
  lib/api.ts, types.ts
  components/TopBar.tsx, Skeleton.tsx, Toast.tsx, EmptyState.tsx, GenreChip.tsx
  features/
    search/useSearch.ts, SearchBar.tsx, SeriesCard.tsx, SearchPage.tsx
    series/useSeriesDetail.ts, SeriesHero.tsx, SeasonAccordion.tsx, ProgressBar.tsx, SeriesPage.tsx
    episode/useEpisodeTracking.ts, EpisodeRow.tsx
    comments/useComments.ts, CommentList.tsx, CommentForm.tsx
    insight/useInsight.ts, InsightCard.tsx
```

### Hooks

- `useSearch(query)` — 300ms debounce, AbortController, cancels stale requests
- `useSeriesDetail(showId)` — parallel fetch detail + seasons
- `useEpisodeTracking(showId, seasons)` — optimistic toggle, rollback on error
- `useInsight(key, url)` — lazy fetch on click, cache per key

No global store. Two routes, feature hooks. TanStack Query is the upgrade path.

---

## 6. AI Integration

Protocol → ResilientInsightProvider → HuggingFace (primary) + Template (fallback)

- **HuggingFaceInsightProvider**: POST to HF Inference API, chat-completions, instruct model, 8s timeout
- **TemplateInsightProvider**: Genre-driven tone + summary excerpt, no network, deterministic
- **ResilientInsightProvider**: `asyncio.wait_for(primary, timeout)`, any exception → fallback

Prompt: system = TV critic, spoiler-free, max 120 words. User data in delimiters.

Why HuggingFace: free tier, no credit card, one env var. Works without token (template fallback).

---

## 7. Data Model

Two tables: `watched_episodes` (episode_id UNIQUE, show_id, watched_at) and `comments` (target_type CHECK, target_id, body 1..2000, created_at). No FK to TVMaze. `create_all` on startup (Alembic is next step).

---

## 8. Security

- Pydantic validation at edge; domain re-checks invariants
- `HF_API_TOKEN` backend-only; no `VITE_*` secrets
- httpx timeouts (5s TVMaze, 8s HF); AI errors → fallback, never 5xx
- HTML stripped server-side; comments rendered as text nodes; SQL via SQLAlchemy params

---

## 9. Testing Strategy

- **Domain**: pytest + hypothesis, completion property 0≤c≤1
- **Services**: in-memory fakes, no mocks, no DB
- **AI**: stub providers (sleep/raise), MockTransport for httpx
- **Mapping**: recorded TVMaze JSON fixtures
- **API**: httpx AsyncClient, DI overrides, real Postgres

Unit suite < 2s, no network. Integration against compose Postgres.

---

## 10. Docker & Infrastructure

- `docker-compose.yml` v3.3: postgres:16-alpine (healthcheck) + app (port 7777)
- Multi-stage Dockerfile: node build → python 3.13-slim + uv
- `init_db()` in lifespan with retry
- `make dev`: compose db + uvicorn --reload + vite proxy

---

## 11. Sequencing

- **Phase 1** (A, B, C): Backend vertical slice — 20h
- **Phase 2** (D): Frontend — 14h
- **Phase 3** (E): AI integration — 6h
- **Phase 4** (F, G): Ship — 11h

---

*Seven2U Design Spec v1.0 · beecrowd Software Architect challenge*
