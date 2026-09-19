# Seven2U — Post-Implementation Deck

> Twelve slides on what was built. Companion to `seven2u-post-slides.html`.

---

## 1. Title

**Seven2U** — Interactive TV Series Companion

Never lose where you stopped. *Know what to expect* before watching.

Delivered · beecrowd Software Architect challenge

---

## 2. Problem

Five series in rotation. *Which episode was I on?* Was that one worth it? Is the next one?

Trackers remember checkboxes. Ratings sites remember opinions. Nobody tells you what an episode *is* before you press play.

---

## 3. Solution

Search. Track. **Insight.** One surface, one port.

- **Search** — TVMaze live, debounced, poster grid. Catalogue never mirrored.
- **Track** — watched state and notes in Postgres. Optimistic toggle, per-season progress.
- **Insight** — spoiler-free AI preview via Agno + Groq. Falls back to a heuristic summary, labelled.

---

## 4. Architecture

Clean Architecture. **Domain owns the ports; infrastructure implements them.**

```
                 ┌──────────────────────────────────────────┐
                 │  api/dependencies.py  (composition root) │
                 │  builds adapters, injects into services  │
                 └──────┬───────────────────────┬───────────┘
                        │                       │
   api ──▶ services ──▶ domain  ◀── infrastructure
   routes  use cases    models            TVMazeGateway
   schemas              Protocols         SqlWatchedRepository
   errors               progress          SqlCommentRepository
                        errors            GroqProvider
                                          HeuristicTemplateProvider
```

`domain/interfaces.py` declares `SeriesCatalog`, `WatchedRepository`, `CommentRepository`, `InsightProvider`. Services take them by constructor. Tests inject in-memory fakes.

---

## 5. Sequence — TV series search

```
Browser        React            FastAPI           SeriesService     TVMazeGateway      TVMaze API
  │ types "bre"  │                 │                    │                  │                 │
  │─────────────▶│ 300ms debounce  │                    │                  │                 │
  │              │ abort previous  │                    │                  │                 │
  │              │─GET /series/search?q=breaking───────▶│                  │                 │
  │              │                 │─search("breaking")─▶│                  │                 │
  │              │                 │   trim, 1..100     │─search(q)───────▶│                 │
  │              │                 │                    │                  │ cache hit? ─┐   │
  │              │                 │                    │                  │◀────────────┘   │
  │              │                 │                    │                  │─GET /search/shows?q=─▶
  │              │                 │                    │                  │◀──200 [{show}]───│
  │              │                 │                    │                  │ strip HTML,     │
  │              │                 │                    │                  │ cache 300s      │
  │              │                 │                    │◀─list[Series]────│                 │
  │              │                 │◀─list[Series]──────│                  │                 │
  │              │◀─200 SeriesOut[]│                    │                  │                 │
  │◀ grid ───────│                 │                    │                  │                 │

Empty path:  q="" → 422 ValidationError → SearchBar shows nothing (client never sends blank)
No results:  200 [] → EmptyState "No results found"
Error path:  TVMaze 5xx/timeout → UpstreamError → 502 → ErrorState with Retry
```

---

## 6. Sequence — Series details

```
Browser     React              FastAPI        SeriesService        TVMazeGateway      WatchedRepo (PG)
  │ /series/169 │                  │                │                     │                  │
  │────────────▶│─GET /series/169─▶│                │                     │                  │
  │             │                  │─get_details───▶│                     │                  │
  │             │                  │                │── asyncio.gather ───┼──────────────────┤
  │             │                  │                │  get_series(169) ──▶│ (cache/TVMaze)   │
  │             │                  │                │  get_episodes(169)─▶│ (cache/TVMaze)   │
  │             │                  │                │  ids_for_series(169)──────────────────▶│ SELECT
  │             │                  │                │◀── Series, [Episode], frozenset{ids} ──┤
  │             │                  │                │ group_by_season()   │                  │
  │             │                  │                │  sort seasons asc,  │                  │
  │             │                  │                │  episodes by number,│                  │
  │             │                  │                │  specials last      │                  │
  │             │                  │                │ Season.completion = watched/total      │
  │             │                  │◀─SeriesDetail──│                     │                  │
  │             │◀─200 SeriesDetailOut (seasons[], watched_count, total)  │                  │
  │◀ hero + accordion + progress   │                │                     │                  │

Then, independently (lazy):
  InsightCard      → GET /series/169/insights          → InsightService
  CommentSection   → GET /series/169/comments          → CommentService
  Eye toggle       → PUT /episodes/{id}/watched        → TrackingService (optimistic; rollback + toast on error)
```

---

## 7. AI component

One Protocol. Two providers. The page **never** breaks.

```
                InsightService
                ─────────────────
                build InsightContext
                (series, episode?, total, watched, notes)
                        │
        primary set?  ──┼── no ──▶ HeuristicTemplateProvider
                        │
                       yes
                        ▼
              GroqProvider (Agno)
              Agent(model=Groq("qwen/qwen3.8-27b"),
                    instructions=SYSTEM_PROMPT)
              asyncio.wait_for(agent.arun(prompt), 2.5s)
                        │
             ok ────────┼──────── timeout / exception / empty
              │                              │
              ▼                              ▼
   SeriesInsight(source="llm:groq")   HeuristicTemplateProvider
                                      SeriesInsight(source="heuristic:fallback")
```

- Prompt: spoiler-free TV critic, ≤120 words, untrusted data inside `<summary>` / `<viewer_notes>`.
- Heuristic: synopsis excerpt + genre tone + rating signal + progress phase + note count. Deterministic.
- UI: badge `AI` vs `smart summary` + muted note when fallback.

---

## 8. Data model

Own only what the user creates.

```sql
CREATE TABLE watched_episodes (
    episode_id  INTEGER PRIMARY KEY,          -- idempotent by construction
    series_id   INTEGER NOT NULL,             -- indexed
    watched_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE comments (
    id          UUID PRIMARY KEY,
    series_id   INTEGER NOT NULL,
    episode_id  INTEGER,                      -- NULL = series-level note
    content     TEXT NOT NULL CHECK (length(trim(content)) > 0),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_comments_target ON comments (series_id, episode_id);
```

No FK to TVMaze. `TrackingService` validates the episode belongs to the series before writing. `PUT watched=true` twice returns the same `watched_at`; `watched=false` on an absent row is a no-op.

---

## 9. Docker

`docker compose up --build` → `localhost:7777`. Done.

| Stage / service | What |
|-----------------|------|
| Stage 1 `node:20-alpine` | `npm ci && npm run build` → `dist/` |
| Stage 2 `python:3.13-slim` | `pip install .`, copies `dist/` → `/app/static`, `uvicorn app.main:app` on 7777 |
| `db` `postgres:16-alpine` | healthcheck, named volume, not published |
| `app` | `DATABASE_URL`, `GROQ_API_KEY: ${GROQ_API_KEY:-}` |

Compose v3.3 `depends_on` does not wait for readiness → lifespan runs `wait_for_database` (10 × 1.5s `SELECT 1`) then `create_all`. Observed on first boot: attempt 1 failed, attempt 2 ready. FastAPI mounts `/assets` and serves `index.html` on any unknown path → deep links like `/series/169` reload correctly. Zero CORS.

---

## 10. Testing

53 tests, < 1 s, zero network.

| Suite | Count | Asserts | Tool |
|-------|-------|---------|------|
| Domain | 6 | Seasons sorted, specials last, foreign ids ignored, completion 0..1 | pytest |
| Services | 23 | Blank query 422; episode ∉ series → 404; toggle idempotent; note trimmed; LLM → fallback on error/timeout | In-memory fakes |
| TVMaze gateway | 6 | Mapping, HTML strip, 404 → NotFound, 5xx → Upstream, cache hit | `httpx.MockTransport` |
| Groq provider | 5 | Prompt shape, success, error, empty, timeout | Fake Agno agent |
| API | 11 | Status codes, DTOs, idempotency, 200-on-AI-failure | httpx `ASGITransport` + real SQL repos on `sqlite+aiosqlite` |

Catalogue and LLM swapped via `app.dependency_overrides`; repositories run for real.

---

## 11. Trade-offs

| Decision | Benefit | Accepted limitation |
|----------|---------|---------------------|
| Single implicit user | No auth surface | Multi-user = `user_id` column |
| No catalogue mirror | Always fresh, 2 tables | Every detail hits TVMaze (300s cache) |
| Idempotent `PUT`, not CRUD | Safe retries, easy optimistic UI | No watch history |
| Heuristic fallback, no retry/breaker | Simplest thing that never 5xx | Rule-based text when LLM absent |
| Pydantic as domain | One model layer | Domain imports Pydantic |
| `create_all`, no Alembic | Zero migration tooling | Needed at first schema change |
| In-process TTL cache | No Redis | Per-replica |

---

## 12. Demo

```
docker compose up --build
open http://localhost:7777
```

1. Search **Breaking Bad** → poster grid with rating and genres.
2. Open it → 5 seasons, 62 episodes, progress bars.
3. Read the **Series insight** (violet card) — `AI` badge with a Groq key, `smart summary` without.
4. Mark S01E01 watched → green flash, season 1 jumps to 14%, survives a container restart.
5. Leave a note on the pilot → shows up in the episode insight context.

*Working solution. Architecture a second engineer can extend in an afternoon.*
