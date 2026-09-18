# Seven2U — Vision

## What It Is

Seven2U is the interactive TV series module of an early-stage streaming platform. It lets users discover series, track what they've watched, annotate their journey, and receive AI-powered insights — all in one place.

The name: "Seven" = seventh art (cinema). "2U" = delivered to you, personalized.

## Core Problem

Users watching multiple series lose track of progress, forget where they stopped, and lack a quick way to evaluate whether a new series or episode is worth their time.

## Value Proposition

> "Never lose where you stopped. Know what to expect before watching."

### Pain Relief
- "Which episode was I on?" — watched state persisted per episode
- "I watch 5 series, can't track all" — progress dashboard per series
- "I had a thought about that episode" — comments persisted on series and episodes

### Gains
- "Is this series for me?" — AI insight analyzes tone, themes, style without spoilers
- "What's this episode about before I commit?" — AI preview based on summary + genres
- "I see my progress" — completion percentage per season/series

## Target User

A person who watches multiple TV series and wants organized control over their viewing journey — discovery, tracking, and reflection.

## Product Surfaces

Single-surface web application:
- **Search view** — discover series via TVMaze API
- **Series detail view** — poster, summary, genres, episodes by season, AI insight
- **Episode tracking** — mark watched, leave comments, AI insight per episode

## Technical Context

- **Frontend**: React + Vite + Tailwind CSS
- **Backend**: Python, Clean Architecture, SOLID
- **Database**: Persistent storage (Docker container)
- **AI**: LLM integration behind interface abstraction, graceful fallback
- **Infrastructure**: Docker Compose v3.3, port 7777, single-command startup
- **External API**: TVMaze (search, show details, episodes)

## Design Philosophy

- Usability over aesthetics — clear navigation, loading states, error feedback
- Platform feel, not tool feel — Seven2U should feel like a real streaming companion
- AI as enabler — insights illuminate, never overwhelm
- Progressive disclosure — search first, details on selection, tracking on interaction

## Non-Goals

- User authentication / multi-user
- Video playback
- Social features
- Pixel-perfect design (challenge explicitly says this)
