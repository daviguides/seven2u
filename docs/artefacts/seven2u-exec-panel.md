# Seven2U: Executive Panel

> Never lose where you stopped. **Know what to expect** before watching.

---

## What It Does

Search **TVMaze**, track episodes in **Postgres**, get an insight from an **LLM behind a Protocol**.

User journey: search → detail + seasons → mark watched → comment → AI insight → tracked

---

## Key Architecture Decisions

| Area | Decision | Detail |
|------|----------|--------|
| Backend | **Clean Architecture** | FastAPI. `api → services → repositories → infrastructure`; `domain` imports nothing. Protocols + DI. |
| Data ownership | **User data only** | TVMaze is the catalogue. Postgres holds two tables: `watched_episodes`, `comments`. |
| AI | **Pluggable** | `InsightProvider` Protocol. HuggingFace primary, template fallback, 8s timeout. Never a 5xx. |
| Frontend | **React + Vite** | Tailwind, Lucide. Feature folders with `use<Feature>` hooks. No global store. |

---

## Architecture

Five layers, one direction of dependency:

```
api/schemas → services → repositories → infrastructure
                          ↑
                        domain (imports nothing)
```

Protocols: ShowCatalog, WatchedRepository, CommentRepository, InsightProvider

---

## API Overview

| Endpoint | Purpose |
|----------|---------|
| `GET /api/shows/search?q=` | TVMaze search, mapped to domain |
| `GET /api/shows/{id}` | Detail, summary HTML stripped |
| `GET /api/shows/{id}/episodes` | Seasons with watched flags + completion |
| `PUT /api/shows/{id}/episodes/{ep}/watched` | Idempotent set; validates episode belongs to show |
| `GET\|POST /api/comments/{show\|episode}/{id}` | Polymorphic comments |
| `GET /api/insights/shows/{id}[/episodes/{ep}]` | Insight; `source: llm \| fallback` |

---

## AI Integration

One Protocol, two providers, zero failure modes visible to the user.

| Component | Role | Detail |
|-----------|------|--------|
| InsightProvider | Protocol | `generate(InsightRequest) → Insight`. Services see nothing else. |
| HuggingFace Inference | Primary | Chat-completions, instruct model, spoiler-free prompt with delimited data. Token in backend env only. |
| Template provider | Fallback | Genre-driven tone + summary excerpt + comment count. Used on timeout, error, empty text, or missing token. |

### Request Budget

| Service | Latency |
|---------|---------|
| TVMaze | 200-600ms |
| Postgres | <10ms |
| HF LLM | 2-6s |
| Fallback | <1ms |
| **AI timeout cap** | **8s** |

---

## Delivery

Docker Compose v3.3, port **7777**, one command.

- **Multi-stage Dockerfile**: Node builds the SPA; Python 3.13 + uv serves API and static from one process.
- **docker compose up --build**: Postgres 16 with healthcheck; app waits, runs `create_all`, listens on 7777.
- **.env optional**: No token = fallback insights. `HF_API_TOKEN` set = real LLM. Same schema both ways.

---

## Implementation Phases

| Phase | Hours | Scope |
|-------|-------|-------|
| Phase 1 · Backend slice | 20h | Setup, domain, Protocols, fakes, TVMaze client, services, routes. Curl-usable, tests green. |
| Phase 2 · Frontend | 14h | Search, detail, seasons, optimistic watched toggle, comments, insight card. |
| Phase 3 · AI | 6h | Protocol, template fallback, resilient wrapper, HuggingFace adapter, routes. |
| Phase 4 · Ship | 11h | Dockerfile, compose, integration tests on compose DB, smoke script, README. |

---

## Summary

| Metric | Value |
|--------|-------|
| Total effort | **51h** |
| Tasks | 40 tasks, 7 workstreams |
| Solo calendar | **7 days** |
| Critical path | ~24h. Pushed pace: 5 days. |

---

*Seven2U Executive Panel · beecrowd Software Architect challenge*
