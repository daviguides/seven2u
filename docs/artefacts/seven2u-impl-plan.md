# Seven2U Implementation Plan v1.0

> 40 tasks across 7 workstreams. 51 hours total. Critical path ~24h. Solo developer: 7 working days at a sustainable pace, 5 if pushed. Every task names the test it starts with.

beecrowd Software Architect challenge · companion to the design spec

---

## Workstreams

| WS | Name | Hours | Tasks |
|----|------|-------|-------|
| A | Setup | 4h | 4 |
| B | Domain + services | 10h | 7 |
| C | API | 6h | 5 |
| D | Frontend | 14h | 9 |
| E | AI | 6h | 5 |
| F | Docker | 4h | 3 |
| G | Tests + README | 7h | 7 |

---

## WS-A: Project Setup — 4h

| ID | Task | Files | Dep | Hours | Done when |
|----|------|-------|-----|-------|-----------|
| A1 | Repo scaffold: `backend/` with uv + pyproject (ruff 80 cols, mypy strict, pytest, pytest-asyncio, hypothesis), `.gitignore`, `.env.example`, Makefile targets `dev / test / lint / up` | `backend/pyproject.toml`, `Makefile`, `.env.example` | none | 1h | `uv sync` clean. `make lint` passes on empty package. |
| A2 | FastAPI skeleton: `create_app()`, `Settings` via pydantic-settings, `/api/health`, lifespan hook | `app/main.py`, `app/config.py`, `app/api/routes/health.py`, `tests/integration/test_health.py` | A1 | 1h | Health returns 200 with `{status:"ok"}` under httpx AsyncClient. |
| A3 | Frontend scaffold: Vite + React + TS + Tailwind + lucide-react; design tokens from design-system.md as Tailwind theme; Vite proxy `/api -> :7777` | `frontend/`, `tailwind.config.ts`, `vite.config.ts` | none | 1h | `npm run dev` shows TopBar with logo in dark palette. `npm run build` emits `dist/`. |
| A4 | README skeleton: sections for run, architecture, trade-offs, AI, tests (filled by G7) | `README.md` | none | 1h | Headings present; run command copy-pasteable once F2 lands. |

---

## WS-B: Backend Domain + Services — 10h

### Domain (no framework imports)

| ID | Task | Files | Dep | Hours | Done when |
|----|------|-------|-----|-------|-----------|
| B1 | Domain models as frozen dataclasses + errors | `app/domain/models.py`, `app/domain/errors.py`, `tests/unit/domain/test_models.py` | A1 | 1.5h | Test: models are immutable, `CommentTarget("show")` parses, errors subclass a common `DomainError`. |
| B2 | Season grouping + completion rule | `app/domain/progress.py`, `tests/unit/domain/test_progress.py` | B1 | 1.5h | Tests: empty season = 0.0; all watched = 1.0; foreign watched IDs ignored; hypothesis property 0≤c≤1; seasons sorted ascending. |
| B3 | Repository Protocols + in-memory fakes | `app/repositories/protocols.py`, `tests/fakes.py` | B1 | 1h | mypy accepts fakes where Protocols are expected. Fakes have a `seed()` helper. |

### Infrastructure + services

| ID | Task | Files | Dep | Hours | Done when |
|----|------|-------|-----|-------|-----------|
| B4 | TVMaze client: httpx AsyncClient, 5s timeout, mapping raw JSON to domain, HTML stripping, 404 to `NotFoundError`, 5xx/timeout to `UpstreamError`, 60s in-process TTL cache | `app/infrastructure/tvmaze/client.py`, `mapping.py`, `tests/unit/infra/test_tvmaze_mapping.py`, `tests/fixtures/tvmaze/*.json` | B3 | 2.5h | Fixture for search/show/episodes maps correctly; missing image and null summary tolerated; `<p>` stripped. |
| B5 | ShowService + TrackingService | `app/services/show_service.py`, `tracking_service.py`, `tests/unit/services/test_show_service.py`, `test_tracking_service.py` | B2, B3 | 1.5h | Tests: empty query raises ValidationError; `set_watched` for episode outside show raises NotFoundError; set true twice is idempotent; `episodes_with_progress` returns seasons with correct completion. |
| B6 | CommentService | `app/services/comment_service.py`, `tests/unit/services/test_comment_service.py` | B3 | 1h | Tests: body trimmed; whitespace-only rejected; list ordered by created_at asc. |
| B7 | SQLAlchemy tables + async session + Sql repositories + `init_db()` | `app/infrastructure/db/session.py`, `tables.py`, `watched_repository.py`, `comment_repository.py` | B3 | 1h | Upsert on `episode_id` UNIQUE; unmark is a no-op when absent. Verified by G3 against Postgres. |

---

## WS-C: Backend API — 6h

| ID | Task | Files | Dep | Hours | Done when |
|----|------|-------|-----|-------|-----------|
| C1 | Pydantic schemas for shows, tracking, comments, insights | `app/api/schemas/*.py` | B1 | 1h | Schemas match spec §4 field-for-field. `from_domain()` classmethods. |
| C2 | Dependency wiring: session per request, service factories, catalog singleton | `app/api/deps.py` | B5, B6, B7 | 1h | Services constructed only in `deps.py`. Overridable via `app.dependency_overrides`. |
| C3 | Shows routes: search + detail | `app/api/routes/shows.py`, `tests/integration/test_shows_api.py` | C1, C2 | 1h | Tests with StubCatalog: search returns list; unknown ID 404; `q` over 100 chars 422. |
| C4 | Tracking + comments routes | `app/api/routes/tracking.py`, `comments.py`, `tests/integration/test_tracking_api.py`, `test_comments_api.py` | C1, C2 | 1.5h | PUT watched twice = same response; GET episodes reflects state; POST comment 201; invalid target 422. |
| C5 | Error mapping middleware + CORS (dev only) + static SPA mount | `app/api/errors.py`, `app/main.py` | C3, C4 | 1.5h | NotFound 404, Validation 422, Upstream 502, unexpected 500 with generic body. `/` serves index.html when `static/` exists. |

---

## WS-D: Frontend — 14h

| ID | Task | Files | Dep | Hours | Done when |
|----|------|-------|-----|-------|-----------|
| D1 | API client + types mirroring schemas; `ApiError` with status | `src/lib/api.ts`, `src/lib/types.ts` | A3, C1 | 1h | Typed functions for every endpoint. Non-2xx throws ApiError. |
| D2 | Layout: TopBar, router (`/`, `/shows/:id`), Toast, Skeleton, EmptyState | `src/App.tsx`, `src/components/*.tsx` | A3 | 1.5h | Navigation works; back arrow on detail; toast can be triggered. |
| D3 | Search feature: `useSearch` (300ms debounce, AbortController), SearchBar, SeriesCard grid | `src/features/search/*` | D1, D2 | 2.5h | Typing "breaking" shows cards; stale responses discarded; empty and no-results states render. |
| D4 | Series detail: `useSeriesDetail` (parallel fetch), SeriesHero, SeasonAccordion, ProgressBar | `src/features/series/*` | D1, D2 | 3h | Hero + seasons render; skeleton while loading; error card with retry on 502. |
| D5 | Episode tracking: `useEpisodeTracking` optimistic toggle with rollback, EpisodeRow with Eye/EyeOff, green flash | `src/features/episode/*` | D4 | 2h | Toggle updates row + season progress instantly; refresh persists; failed PUT rolls back + toast. |
| D6 | Comments: `useComments`, CommentList, CommentForm (series + episode targets) | `src/features/comments/*` | D4 | 2h | Post appends to list; empty submit disabled; count badge on EpisodeRow. |
| D7 | Insight: `useInsight` lazy load + cache, InsightCard with violet border, pulse skeleton, fallback note | `src/features/insight/*` | D4, E5 | 1.5h | Series and episode insight render; `source:"fallback"` shows muted note instead of AI badge. |
| D8 | Polish: responsive grid breakpoints, `prefers-reduced-motion`, focus rings, light mode tokens | `src/index.css`, components | D3-D7 | 0.5h | Mobile single column; tablet 2; desktop 3-4. Keyboard reachable. |
| D9 | Production build wired: `npm run build` output consumed by C5 static mount | `vite.config.ts` (base), `app/main.py` | D8, C5 | 1h | Backend serves SPA at `/`; deep link `/shows/82` reloads correctly. |

---

## WS-E: AI Integration — 6h

| ID | Task | Files | Dep | Hours | Done when |
|----|------|-------|-----|-------|-----------|
| E1 | `InsightProvider` Protocol, `InsightRequest`, `Insight`, prompt builder with delimiters | `app/infrastructure/ai/protocol.py`, `prompt.py`, `tests/unit/ai/test_prompt.py` | B1 | 1h | Prompt contains title, genres, delimited summary and comments; word cap stated. |
| E2 | `TemplateInsightProvider`: deterministic, genre-driven tone + summary excerpt + comment count | `app/infrastructure/ai/template.py`, `tests/unit/ai/test_template_provider.py` | E1 | 1h | Exact-string tests for 3 genre combos; empty summary handled. |
| E3 | `ResilientInsightProvider`: timeout via `asyncio.wait_for`, exception and empty-text fallback, logging, `primary=None` mode | `app/infrastructure/ai/resilient.py`, `tests/unit/ai/test_resilient_provider.py` | E2 | 1.5h | Stub that sleeps 10s returns fallback within timeout; stub that raises returns fallback; provider name reported correctly. |
| E4 | `HuggingFaceInsightProvider`: httpx to HF chat-completions, model from settings, 8s timeout, response parsing | `app/infrastructure/ai/huggingface.py`, `tests/unit/ai/test_huggingface_provider.py` | E1 | 1.5h | Mocked transport: 200 parses text; 503 raises; malformed JSON raises. Manual smoke with real token documented. |
| E5 | `InsightService` + insight routes + provider selection in `deps.py` (token present = HF, else template) | `app/services/insight_service.py`, `app/api/routes/insights.py`, `tests/unit/services/test_insight_service.py`, `tests/integration/test_insights_api.py` | E3, E4, C2 | 1h | Service passes comments into request; API returns 200 with `source:"fallback"` when provider raises; health reports provider name. |

---

## WS-F: Docker + Infra — 4h

| ID | Task | Files | Dep | Hours | Done when |
|----|------|-------|-----|-------|-----------|
| F1 | Multi-stage Dockerfile: node build stage, python 3.13-slim + uv runtime, copies `dist/` to `static/` | `Dockerfile`, `.dockerignore` | D9 | 2h | Image builds under 2 min warm; size under 300MB; runs with `docker run -p 7777:7777` against an external DB. |
| F2 | `docker-compose.yml` v3.3: db (postgres:16-alpine, healthcheck, named volume), app (depends_on healthy, env passthrough for HF) | `docker-compose.yml` | F1 | 1h | `docker compose up --build` from clean clone reaches healthy in one command; port 7777 open; DB not exposed. |
| F3 | Startup: `init_db()` in lifespan with retry (5 x 2s) for DB readiness; `make up` alias | `app/main.py`, `app/infrastructure/db/session.py`, `Makefile` | F2 | 1h | Tables exist after first boot; second boot is idempotent; restart with volume keeps data. |

---

## WS-G: Testing + README — 7h

| ID | Task | Files | Dep | Hours | Done when |
|----|------|-------|-----|-------|-----------|
| G1 | Domain suite hardening: hypothesis strategies for episodes/seasons, edge cases (duplicate episode IDs, season 0 specials) | `tests/unit/domain/` | B2 | 1h | Property tests pass 200 examples; specials grouped as season 0. |
| G2 | Service suite: batch-table tests via `pytest.mark.parametrize` for tracking and comment invariants | `tests/unit/services/` | B5, B6 | 1.5h | Every service method has happy + 2 failure cases. Coverage of `app/services` 100%. |
| G3 | Integration conftest: app against compose Postgres, truncate between tests, DI overrides for catalog + provider | `tests/integration/conftest.py` | C5, F2 | 1.5h | `make test` runs unit then integration; integration skipped with clear message when DB unreachable. |
| G4 | AI suite: resilient + template + prompt + HF mocked transport | `tests/unit/ai/` | E3, E4 | 0.5h | No test touches the network (assert via `httpx.MockTransport`). |
| G5 | Frontend tests: vitest for `useSearch` debounce/abort and `useEpisodeTracking` optimistic rollback | `src/features/**/*.test.ts` | D3, D5 | 1h | 4 tests green in `npm test`. |
| G6 | End-to-end smoke script: compose up, curl health, search, detail, toggle, comment, insight | `scripts/smoke.sh` | F3 | 0.5h | Script exits 0 on fresh clone with no HF token (fallback path) and with token. |
| G7 | README final: run in one command, architecture diagram (ASCII), layer table, AI provider + fallback, trade-offs, what I'd do next (auth, Alembic, TanStack Query, caching) | `README.md` | G6 | 1h | A reviewer can run and evaluate without asking a question. |

---

## Execution Waves

### Wave 0: Foundations — Day 1 (4h)

| Track | Tasks | Notes |
|-------|-------|-------|
| Backend | A1, A2 | Lint + test harness green before any feature |
| Frontend | A3 | Tailwind theme from design-system.md |
| Docs | A4 | README skeleton, filled at the end |

### Wave 1: Domain + infrastructure — Days 1-2 (10h)

| Track | Tasks | Notes |
|-------|-------|-------|
| Domain (test first) | B1, B2, B3 | Fakes written alongside Protocols |
| Adapters | B4, B7 | TVMaze fixtures recorded once, committed |
| Services | B5, B6 | Unit suite runs with zero I/O |
| AI core | E1, E2, E3 | Fallback exists before the real provider |

### Wave 2: API surface — Days 2-3 (8h)

| Track | Tasks | Notes |
|-------|-------|-------|
| Routes | C1, C2, C3, C4, C5 | Backend usable via curl end of day 3 |
| AI provider | E4, E5 | HF adapter with mocked transport; real smoke manual |
| Tests | G1, G2, G4 | Unit coverage locked before frontend starts |

### Wave 3: Frontend — Days 4-5 (14h)

| Track | Tasks | Notes |
|-------|-------|-------|
| Core screens | D1, D2, D3, D4 | Against live backend via Vite proxy |
| Interactions | D5, D6, D7 | Optimistic toggle is the riskiest UI piece; test it (G5) |
| Polish | D8, G5 | Responsive + reduced motion |

### Wave 4-5: Ship — Days 6-7 (9h)

| Track | Tasks | Notes |
|-------|-------|-------|
| Build | D9, F1, F2, F3 | One command from clean clone |
| Verification | G3, G6 | Integration suite against compose DB; smoke script both AI paths |
| Delivery | G7 | README with trade-offs; push public repo |

---

## Non-Goals and Guardrails

1. No authentication or multi-user. Single implicit user; `user_id` is the documented next step.
2. No catalogue mirroring. TVMaze is read live (with a 60s in-process cache); the DB holds only user-generated rows.
3. No agent framework. One inference call behind a Protocol; Agno-style orchestration is out of scope.
4. No global state library on the frontend. Two routes, feature hooks. TanStack Query is the named upgrade path.
5. No Alembic. `create_all` for two greenfield tables; migration tooling listed under "next steps".
6. No pixel-perfect UI. Usability, states and clarity over aesthetics, per the challenge brief.

---

## Cross-Cutting Reminders

- **Domain imports nothing** — B1/B2 must not import Pydantic, SQLAlchemy or FastAPI. Enforced by a ruff `banned-api` rule in `pyproject.toml` (A1).
- **Services never see HTTP** — No status codes, no Request objects. Error mapping lives only in C5.
- **AI never 5xx** — E3 guarantees every path returns an `Insight`. The API test in E5 asserts 200 when the provider raises.
- **Episode belongs to show** — B5 validates against the catalogue before writing. Otherwise the DB accepts any integer pair.
- **Test first, every task** — Each row names its test file. Red before green. Fixtures over mocks; `MockTransport` only at the httpx edge.
- **No secrets in the image** — `HF_API_TOKEN` comes from compose env at runtime. `.env` is in `.dockerignore` and `.gitignore`.

---

## Summary

- **40 tasks**, 7 workstreams
- **51 hours** total effort
- **~24h critical path** (3 working days if nothing else existed)

### Calendar Estimate (solo developer)

| Pace | Hours/day | Calendar days | Notes |
|------|-----------|---------------|-------|
| Sustainable | 7-8 | 7 | Waves as laid out; one day of slack for HF API surprises |
| Pushed | 10 | 5 | Frontend polish (D8) and property tests (G1) trimmed to essentials |
| Part-time | 4 | 13 | Same order; AI and Docker waves fit evenings |

### Critical Path

```
A1(1h) > A2(1h) > B1(1.5h) > B3(1h) > B5(1.5h) > C2(1h) > C4(1.5h) > C5(1.5h)
> D1(1h) > D4(3h) > D5(2h) > D9(1h) > F1(2h) > F2(1h) > F3(1h) > G6(0.5h) > G7(1h)
Total: ~24h
```

### Launch Gate Checklist

- [ ] `docker compose up --build` from a fresh clone serves the app on :7777 with no extra steps
- [ ] Search, detail, episodes, watched toggle, comments work end to end (G6 smoke)
- [ ] Watched state and comments survive `docker compose restart`
- [ ] Insight returns 200 with and without `HF_API_TOKEN`; fallback visibly labelled in UI
- [ ] `make test`: unit suite green with no network; integration suite green against compose DB
- [ ] `make lint`: ruff + mypy strict clean; domain has zero framework imports
- [ ] README documents run, architecture, AI fallback, trade-offs, next steps
- [ ] No secret in repo history; `.env.example` committed

---

*Seven2U Implementation Plan v1.0 · beecrowd Software Architect challenge*
