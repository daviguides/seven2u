# Seven2U — Post-Implementation Executive Panel

> What was actually built. One screen. Reflects the code on `main` as of 2026-09-18, not the design spec.

beecrowd Software Architect challenge · Delivered

---

## What Seven2U does

**"Never lose where you stopped. Know what to expect before watching."**

A user searches a series (TVMaze), opens its detail page, sees episodes grouped by season with a progress bar each, marks episodes watched, leaves notes on the series or an episode, and reads a spoiler-free AI insight. One origin, one port, one command.

Journey: `search` → `detail + seasons` → `mark watched` → `note` → `AI insight`.

---

## Architecture delivered

Clean Architecture with the domain owning the ports. Dependencies point inward; the composition root (`api/dependencies.py`) is the only place concrete adapters are instantiated.

```
api ──▶ services ──▶ domain ◀── infrastructure
 │                     ▲
 └── dependencies.py ──┘  (composition root: builds adapters, injects into services)
```

| Layer | Modules (real) | Responsibility |
|-------|----------------|----------------|
| `domain` | `models.py`, `interfaces.py`, `progress.py`, `errors.py` | Frozen Pydantic models; Protocols `SeriesCatalog`, `WatchedRepository`, `CommentRepository`, `InsightProvider`; pure `group_by_season`; `NotFoundError` / `ValidationError` / `UpstreamError` |
| `services` | `series_service.py`, `tracking_service.py`, `comment_service.py`, `insight_service.py` | Use cases. Constructor-injected Protocols. No HTTP, no SQL |
| `infrastructure` | `tvmaze_gateway.py`, `watched_repo.py`, `comment_repo.py`, `db_models.py`, `database.py`, `groq_provider.py`, `heuristic_provider.py` | Concrete adapters: httpx + TTL cache, SQLAlchemy async, Agno agent |
| `api` | `router.py`, `series.py`, `tracking.py`, `comments.py`, `insights.py`, `schemas.py`, `errors.py`, `dependencies.py` | Routes, DTOs with `from_domain()`, domain error → HTTP mapping, DI |

Deviation from spec, on purpose: **Pydantic v2 frozen models are the domain** (no dataclass ↔ Pydantic ↔ ORM triple mapping). SQLAlchemy models exist only in `infrastructure/db_models.py`.

---

## Tech stack

| Tier | Stack |
|------|-------|
| Backend | Python 3.13 · FastAPI · SQLAlchemy 2 async + asyncpg · httpx · Pydantic v2 / pydantic-settings · **Agno 3 + Groq** |
| Frontend | React 19 · React Router 7 · Vite 6 · Tailwind 3 · Lucide · TypeScript strict |
| Data | PostgreSQL 16 (alpine), named volume |
| Delivery | Multi-stage Dockerfile (node:20-alpine → python:3.13-slim) · Docker Compose v3.3 · port 7777 |
| Quality | Ruff (80 cols, google docstrings) · pytest + pytest-asyncio · aiosqlite for API tests |

---

## API surface (as shipped, prefix `/api/v1`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness |
| GET | `/series/search?q=` | TVMaze search, HTML stripped, 1..100 chars |
| GET | `/series/{id}` | Series + seasons + episodes with `watched` flag, per-season `completion`, totals |
| PUT | `/episodes/{id}/watched` | Body `{series_id, watched}`. Idempotent end-state. Validates episode ∈ series |
| GET | `/series/{id}/comments[?episode_id=]` | Notes for series (no `episode_id`) or one episode |
| POST | `/series/{id}/comments[?episode_id=]` | Add note, trimmed, 1..2000 chars → `201` |
| GET | `/series/{id}/insights` | Series insight, always `200` |
| GET | `/series/{id}/insights/episodes/{ep}` | Episode insight, always `200` |

Errors: `404` unknown series/episode · `422` invalid input · `502` TVMaze down. Insights never 5xx.

---

## AI integration

| Piece | Reality |
|-------|---------|
| Port | `InsightProvider.generate_insight(InsightContext) -> SeriesInsight` |
| Primary | `GroqProvider`: Agno `Agent(model=Groq(id, api_key, max_tokens=220, temperature=0.7), instructions=SYSTEM_PROMPT)`; `await asyncio.wait_for(agent.arun(prompt), 2.5)` |
| Model | `qwen/qwen3.8-27b` (Groq free tier), overridable via `GROQ_MODEL` |
| Prompt | Spoiler-free TV critic, ≤120 words; series/episode/genres/progress + `<summary>` and `<viewer_notes>` delimited |
| Fallback | `HeuristicTemplateProvider`: synopsis excerpt + genre tone (25 genres mapped) + rating signal + progress phase (not started / early / final stretch / complete) + note count |
| Policy | No retry, no circuit breaker. Timeout, exception or empty text → fallback. No key → fallback directly |
| Contract | `source: "llm:groq" \| "heuristic:fallback"`; UI shows `AI` or `smart summary` badge |

---

## Key metrics

| Metric | Value |
|--------|-------|
| Tests | **53 passing**, < 1s, zero network (42 unit · 11 integration) |
| Commits | **11** on `main` (1 docs + 10 implementation) |
| Containers | **2** (`app`, `db`) |
| Exposed port | **7777** only |
| Startup | `docker compose up --build` |
| Backend modules | 24 Python files, every one with a module docstring |
| Frontend | 10 components · 3 feature folders · 4 hooks · 2 routes |

---

## Conscious trade-offs

| Decision | Benefit | Accepted limitation |
|----------|---------|---------------------|
| Single implicit user | No auth surface, faster delivery | Multi-user = add `user_id` to both tables |
| External catalogue, never mirrored | Zero sync, always fresh, 2 tables total | Every detail page hits TVMaze (mitigated by 300s TTL cache) |
| Idempotent `PUT watched`, not CRUD | Safe retries, trivial optimistic UI | No watch history, only current state |
| Local heuristic fallback | Page never breaks; works with no key | Fallback is rule-based, honestly labelled |
| Pydantic as domain model | One model layer, less mapping code | Domain depends on Pydantic (framework-light, not framework-free) |
| `create_all`, no Alembic | Two greenfield tables, no migration tooling | First schema change needs migrations |
| In-process TTL cache | No Redis | Per-replica; scale-out needs shared cache |

---

## What's running (verified)

- `docker compose up --build` from clean state: DB retry loop observed (attempt 1 failed, attempt 2 ready), tables created, app on 7777.
- Live TVMaze: search "breaking" → 10 results; `/series/169` → 5 seasons, 62 episodes, HTML stripped.
- Watched toggle persisted; survived `docker compose restart app`.
- Notes on series and episode stored separately; blank note → 422.
- Insight without key → `heuristic:fallback`, reflects progress and note count. With `GROQ_API_KEY` → `llm:groq` via Agno + qwen3.8-27b.
- UI checked in browser (desktop + 390px mobile): search grid, detail, accordion, toggle, no console errors.

Bugs caught in verification and fixed: `asyncio.gather` over a shared `AsyncSession` (Postgres-only failure, SQLite masked it); duplicate native clear button on search input.

---

*Seven2U Post-Implementation Panel · beecrowd Software Architect challenge*
