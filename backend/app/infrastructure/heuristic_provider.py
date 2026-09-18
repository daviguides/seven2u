"""Deterministic, rule-based InsightProvider used as a fallback."""

from app.domain.models import InsightContext, SeriesInsight

GENRE_TONES: dict[str, str] = {
    "Drama": "emotionally grounded, character-driven storytelling",
    "Comedy": "a light, quick-witted rhythm",
    "Crime": "moral tension and slow-burning consequences",
    "Thriller": "sustained suspense that rewards attention",
    "Horror": "dread that builds scene by scene",
    "Science-Fiction": "big ideas explored through speculative worlds",
    "Fantasy": "world-building with its own rules and mythology",
    "Mystery": "puzzle-box plotting where details matter",
    "Romance": "relationships at the emotional core",
    "Action": "kinetic set pieces and momentum",
    "Adventure": "a journey structure with escalating stakes",
    "Anime": "stylised visuals and serialized arcs",
    "Family": "warm, accessible storytelling for every age",
    "Supernatural": "the uncanny bleeding into everyday life",
    "History": "period detail and real-world resonance",
    "War": "human cost set against large-scale conflict",
    "Western": "frontier morality and wide-open spaces",
    "Legal": "procedural rigor and ethical dilemmas",
    "Medical": "high-pressure decisions with lives on the line",
    "Music": "performance and rhythm woven into the narrative",
    "Espionage": "double-crosses and shifting loyalties",
    "Children": "playful, gentle pacing",
    "Sports": "competition and discipline as character study",
    "Travel": "place as a character in itself",
    "Nature": "the natural world observed with patience",
}

DEFAULT_TONE = "a distinctive voice that reveals itself over time"
EXCERPT_CHARS = 180
PROGRESS_NOT_STARTED = 0.0
PROGRESS_LATE = 0.75
PROGRESS_COMPLETE = 1.0
HIGH_RATING = 8.0
MAX_HIGHLIGHTS = 3


def _tone_sentence(genres: tuple[str, ...]) -> str:
    tones = [GENRE_TONES[g] for g in genres if g in GENRE_TONES]
    if not tones:
        return f"Expect {DEFAULT_TONE}."
    if len(tones) == 1:
        return f"Expect {tones[0]}."
    return f"Expect {', '.join(tones[:-1])} and {tones[-1]}."


def _excerpt(summary: str | None) -> str:
    if not summary:
        return "No official synopsis is available yet."
    if len(summary) <= EXCERPT_CHARS:
        return summary
    cut = summary[:EXCERPT_CHARS].rsplit(" ", 1)[0]
    return f"{cut}…"


def _progress_sentence(context: InsightContext) -> str:
    total = context.total_episodes
    if total == 0:
        return ""
    ratio = context.watched_count / total
    if ratio == PROGRESS_NOT_STARTED:
        return (
            f"You have not started yet: {total} episodes are waiting, so "
            "settle in for the opening chapters that set the rules."
        )
    if ratio >= PROGRESS_COMPLETE:
        return (
            "You have watched every episode; this is the moment to "
            "revisit favourites or reflect on how the arcs paid off."
        )
    if ratio >= PROGRESS_LATE:
        return (
            f"You are {context.watched_count} of {total} in, deep into "
            "the final stretch where threads start converging."
        )
    return (
        f"You have seen {context.watched_count} of {total} episodes, so "
        "the groundwork is laid and the stakes are about to rise."
    )


def _rating_sentence(rating: float | None) -> str:
    if rating is None:
        return ""
    if rating >= HIGH_RATING:
        return f"Viewers rate it {rating:.1f}/10, a strong signal it delivers."
    return f"Viewers rate it {rating:.1f}/10."


def _comments_sentence(count: int) -> str:
    if count == 0:
        return ""
    noun = "note" if count == 1 else "notes"
    return f"You have left {count} {noun} along the way."


class HeuristicTemplateProvider:
    """Builds insights from genres, summary, rating and viewer progress."""

    async def generate_insight(self, context: InsightContext) -> SeriesInsight:
        """Compose a deterministic, spoiler-free insight."""
        series = context.series
        if context.episode is not None:
            ep = context.episode
            lead = (
                f"S{ep.season}E{ep.number or '?'} “{ep.name}” of "
                f"{series.name}. {_excerpt(ep.summary or series.summary)}"
            )
        else:
            lead = f"{series.name}. {_excerpt(series.summary)}"

        parts = [
            lead,
            _tone_sentence(series.genres),
            _rating_sentence(series.rating),
            _progress_sentence(context),
            _comments_sentence(len(context.comments)),
        ]
        text = " ".join(p for p in parts if p)
        return SeriesInsight(
            text=text,
            highlights=tuple(series.genres[:MAX_HIGHLIGHTS]),
            source="heuristic:fallback",
        )
