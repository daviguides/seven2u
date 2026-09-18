# Seven2U

Interactive TV series companion: search series (TVMaze), track watched episodes, leave notes on series and episodes, and get a spoiler-free AI insight before you press play.

> "Seven" = seventh art. "2U" = delivered to you.

## Run it

```bash
docker compose up --build
```

Open <http://localhost:7777>. That is the only exposed port: FastAPI serves both the compiled React SPA and the JSON API from one container; PostgreSQL runs in a second container and is not exposed.

Optional: set `GROQ_API_KEY` (copy `.env.example` to `.env`) to enable LLM-generated insights via Agno + Groq. Without it, or whenever the model is slow or fails, the app falls back to a rule-based insight and labels it as such in the UI. Nothing breaks either way.

## What you can do

| Feature | Where |
|---------|-------|
| Search series by name (debounced, cancels stale requests) | `/` |
| Series detail: poster, genres, rating, synopsis, overall progress | `/series/:id` |
| Episodes grouped by season with per-season progress bars | detail page, accordion |
| Mark episodes watched / unwatched (optimistic, rolls back on error) | eye icon per episode |
| Notes on the series or on a single episode | notes panels |
| AI insight for the series or for one episode | violet card, sparkle icon |
| Dark / light theme | top-right toggle |

## Architecture

```
frontend/ (React 19 + Vite + Tailwind)  ──build──▶  backend/static/  (served at /)
                                                          │
backend/app/                                              ▼
  api/            routes, DTOs, DI wiring, error mapping   ◀── HTTP /api/v1/*
  services/       use cases (search, detail, tracking, comments, insights)
  domain/         Pydantic frozen models, Protocols, pure season rules
  infrastructure/ TVMaze gateway, SQLAlchemy repos, Agno/Groq + heuristic providers
```

Dependency rule: `api → services → domain ← infrastructure`. Services depend only on the Protocols in `domain/interfaces.py`; concrete adapters are injected in `api/dependencies.py`. Unit tests replace every adapter with in-memory fakes (`tests/fakes.py`), so the service suite runs with zero I/O.

### Key decisions

- **Own only user data.** TVMaze is the source of truth for shows and episodes and is never mirrored. Postgres holds two tables: `watched_episodes` and `comments`. A 300s in-process TTL cache keeps TVMaze calls low and avoids rate limiting.
- **Pydantic is the domain model.** Frozen Pydantic v2 models serve as domain entities; SQLAlchemy models live only in `infrastructure/`. One mapping (domain ↔ DB) instead of three.
- **AI is a plug.** `InsightProvider` is a Protocol. `GroqProvider` runs a single-turn [Agno](https://github.com/agno-agi/agno) `Agent` backed by a Groq chat model (`llama-3.3-70b-versatile` by default, free tier) wrapped in `asyncio.wait_for` with a strict 2.5s timeout; it fails fast. No tools, memory or teams: Agno gives a provider-agnostic model layer so swapping Groq for another vendor is a one-line change. `HeuristicTemplateProvider` builds a real insight from genres, rating, viewer progress and note count. `InsightService` tries the LLM and falls back on any exception. No retries, no circuit breaker: simplest thing that never produces a 5xx. The response carries `source: "llm:groq" | "heuristic:fallback"` so the UI can label it.
- **Idempotent tracking.** `PUT /api/v1/episodes/{id}/watched` with `{"series_id", "watched"}` sets an end state rather than toggling; repeating the call is safe. The service verifies the episode belongs to the series before writing.
- **Single origin.** Multi-stage Dockerfile: Node builds the SPA, Python image serves it plus a catch-all that returns `index.html` for client-side routes. No CORS configuration needed.
- **DB readiness.** Compose v3.3 `depends_on` does not wait for Postgres. The lifespan runs `wait_for_database` (10 × 1.5s) before `create_all`.
- **Async end to end.** FastAPI handlers, `httpx.AsyncClient` for TVMaze, `Agent.arun` for Groq, `asyncpg` through SQLAlchemy's async engine.

## API

All routes under `/api/v1`.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness |
| GET | `/series/search?q=` | Search TVMaze |
| GET | `/series/{id}` | Series + seasons + episodes with `watched` flags and progress |
| PUT | `/episodes/{id}/watched` | Body `{"series_id": n, "watched": bool}`; idempotent |
| GET | `/series/{id}/comments[?episode_id=]` | List notes |
| POST | `/series/{id}/comments[?episode_id=]` | Add note, `201` |
| GET | `/series/{id}/insights` | Series insight |
| GET | `/series/{id}/insights/episodes/{episode_id}` | Episode insight |

Errors: `404` unknown series/episode, `422` invalid input, `502` TVMaze unavailable. Insights never error: provider failure yields `200` with `source: "heuristic:fallback"`.

## Development

```bash
# backend
cd backend && uv venv -p 3.13 .venv && uv pip install -p .venv/bin/python -e ".[dev]"
make test      # 53 tests, no network, in-memory SQLite for the API suite
make lint      # ruff format + ruff check (80 cols, google docstrings)
docker compose up db -d && make dev-backend   # API on :7777

# frontend (proxies /api to :7777)
cd frontend && npm install && npm run dev
```

## Testing strategy

- `tests/unit/`: domain rules (season grouping, completion), every service with fakes, TVMaze mapping and cache via `httpx.MockTransport`, Groq provider (success, error, empty, timeout) via a fake Agno agent, fallback behaviour.
- `tests/integration/test_api.py`: the real FastAPI app with real SQL repositories on `sqlite+aiosqlite` in memory; catalogue and LLM swapped through `app.dependency_overrides`.

## Trade-offs and next steps

- **No auth / single user.** `user_id` on both tables is the first change for multi-user.
- **`create_all` instead of Alembic.** Two greenfield tables; migrations become necessary at the first schema change.
- **In-process cache.** Fine for one replica; Redis if the app scales horizontally.
- **No frontend state library.** Two routes and feature hooks; TanStack Query would add caching and retries for free.
- **Heuristic fallback is honest, not magic.** It is labelled "smart summary" in the UI so users know when the LLM did not answer.
- **Frontend tests.** Not included in this iteration; `useSearch` (debounce/abort) and `useEpisodeTracking` (rollback) are the first candidates for Vitest.
