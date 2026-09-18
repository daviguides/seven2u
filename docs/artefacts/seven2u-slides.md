# Seven2U: Design Deck

---

## Slide 1: Title

# Seven2U

Never lose where you stopped. **Know what to expect** before watching.

---

## Slide 2: The Problem

Five series in rotation. **Which episode was I on?** Was that one worth it? Is the next one?

Trackers remember checkboxes. Ratings sites remember opinions. Nobody tells you what an episode **is** before you press play.

---

## Slide 3: The Move

Search. Track. **Insight.** One surface.

- **Search**: TVMaze, live. Debounced search, poster grid, detail with episodes by season. Catalogue is never mirrored.
- **Track**: Watched + comments. Persisted in Postgres. Optimistic toggle, progress per season, notes on series or episode.
- **Insight**: Spoiler-free AI preview. Tone, themes, who will like it. Personalised by your comments. Falls back gracefully.

---

## Slide 4: Architecture

Clean Architecture. Dependencies point **inward**.

| Layer | Responsibility |
|-------|---------------|
| api | routes, Pydantic schemas, error mapping, DI wiring |
| services | use cases; receive Protocols via constructor |
| repositories | Protocols only: ShowCatalog, Watched, Comment |
| infrastructure | SQLAlchemy, httpx TVMaze client, AI providers |
| **domain** | Series, Episode, Comment, WatchedEpisode, progress rules. Frozen dataclasses. Imports nothing. |

---

## Slide 5: API

Nine endpoints under `/api`. Same origin as the SPA.

| Endpoint | Does |
|----------|------|
| `GET /shows/search?q=` | TVMaze search mapped to domain |
| `GET /shows/{id}/episodes` | Seasons with watched flags and completion ratio |
| `PUT /shows/{id}/episodes/{ep}/watched` | Idempotent. Validates episode belongs to show |
| `GET\|POST /comments/{show\|episode}/{id}` | Polymorphic comments, 1..2000 chars |
| `GET /insights/shows/{id}[/episodes/{ep}]` | Always 200. `source: llm \| fallback` |

---

## Slide 6: AI

One Protocol. Two providers. The page **never** breaks.

- **Primary: HuggingFace** — Chat-completions on an instruct model. Spoiler-free prompt, summary and comments passed as delimited data. Token lives in the backend env only.
- **Fallback: Template** — Genre-driven tone + summary excerpt. Used on 8s timeout, any exception, empty text, or no token. Same schema, labelled `fallback`.

---

## Slide 7: Frontend

Feature folders, `use<Feature>` hooks, presentational components.

```
SearchPage                    SeriesPage
+-- SearchBar (300ms)         +-- SeriesHero
+-- SeriesCard[]              +-- InsightCard (violet)
+-- EmptyState                +-- Comments (target=show)
                              +-- SeasonAccordion[]
Hooks:                            +-- ProgressBar
useSearch (AbortController)       +-- EpisodeRow[]
useSeriesDetail (parallel)            +-- Eye toggle
useEpisodeTracking (optimistic)       +-- InsightCard
useComments                           +-- Comments (target=episode)
useInsight (lazy + cached)
```

---

## Slide 8: Data

Two tables. Own **only** what the user creates.

- **watched_episodes**: episode_id UNIQUE, show_id, watched_at. Upsert on toggle. Index on show_id.
- **comments**: target_type + target_id via CHECK. Body 1..2000. Index on (type, id, created_at).

No FK to TVMaze. IDs are opaque references, validated at write time by the service. Auth later means one `user_id` column, not a redesign.

---

## Slide 9: Docker

`docker compose up --build`. Port **7777**. Done.

- **Stage 1**: node:22-alpine — `npm ci && npm run build`. Emits `dist/`.
- **Stage 2**: python:3.13-slim + uv — Installs locked deps, copies `dist/` to `static/`, serves API + SPA from one uvicorn.
- **DB**: postgres:16-alpine — Healthcheck gates app start. Named volume. Not published to host.

---

## Slide 10: Testing

Fakes over mocks. Domain and services run with **zero I/O**.

| Layer | Asserts | Tool |
|-------|---------|------|
| Domain | Completion in [0,1], foreign IDs ignored, specials as season 0 | pytest + hypothesis |
| Services | Episode must belong to show; toggle idempotent; empty comment rejected | In-memory fakes |
| AI | Timeout, exception, empty text all yield fallback; template deterministic | Stub provider, MockTransport |
| API | Status codes, schemas, 200-on-AI-failure | httpx AsyncClient + compose Postgres |

---

## Slide 11: Plan

**40 tasks**, 7 workstreams, **51h**. Solo: 7 days.

| WS | Hours |
|----|-------|
| A Setup | 4h |
| B Domain | 10h |
| C API | 6h |
| D Frontend | 14h |
| E AI | 6h |
| F Docker | 4h |
| G Tests | 7h |

Critical path ~24h: setup, domain, tracking service, routes, detail page, toggle, build, compose, smoke, README. Every task starts with its test file.

---

## Slide 12: Trade-offs

No catalogue mirror. No auth. No agent framework. No Alembic. **Each one is a named next step, not an oversight.**

Architecture that a second engineer can extend in an afternoon.

---

*Seven2U Design Deck · beecrowd Software Architect challenge*
