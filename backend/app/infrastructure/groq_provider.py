"""Agno + Groq implementation of InsightProvider."""

import asyncio
from typing import Protocol

from agno.agent import Agent
from agno.models.groq import Groq

from app.domain.models import InsightContext, SeriesInsight

GROQ_TIMEOUT_SECONDS = 2.5
GROQ_MAX_TOKENS = 400
GROQ_TEMPERATURE = 0.7
MAX_SUMMARY_CHARS = 800
MAX_COMMENTS_IN_PROMPT = 5
MAX_HIGHLIGHTS = 3

SYSTEM_PROMPT = (
    "You are a thoughtful TV critic writing spoiler-free insights. "
    "Use Smart Brevity format in markdown:\n\n"
    "1. **The hook** — one bold sentence capturing the essence\n"
    "2. **Why it matters** — 2-3 sentences on tone, themes, what "
    "makes it stand out\n"
    "3. **The bottom line** — one sentence: who should watch this "
    "and why\n\n"
    "Use **bold** for key phrases, *italic* for mood/tone words. "
    "Keep it under 150 words. Never reveal plot twists or endings."
)


class GroqProviderError(Exception):
    """Raised when the Groq agent fails, times out or returns nothing."""


class InsightAgent(Protocol):
    """Minimal surface of an Agno Agent used by the provider."""

    async def arun(self, input: str) -> object:  # noqa: A002
        """Run the agent and return an output with a ``content`` attr."""
        ...


def build_prompt(context: InsightContext) -> str:
    """Assemble the user prompt with delimited untrusted data."""
    series = context.series
    lines = [
        f"Series: {series.name}",
        f"Genres: {', '.join(series.genres) or 'unknown'}",
        f"Premiered: {series.premiered or 'unknown'}",
    ]
    if context.episode is not None:
        ep = context.episode
        lines.append(
            f"Episode: S{ep.season}E{ep.number or '?'} — {ep.name}",
        )
        summary = ep.summary or series.summary
    else:
        summary = series.summary
    if context.total_episodes:
        lines.append(
            f"Viewer progress: {context.watched_count} of "
            f"{context.total_episodes} episodes watched",
        )
    lines.append("<summary>")
    lines.append((summary or "No summary available.")[:MAX_SUMMARY_CHARS])
    lines.append("</summary>")
    if context.comments:
        lines.append("<viewer_notes>")
        lines.extend(
            f"- {c}" for c in context.comments[:MAX_COMMENTS_IN_PROMPT]
        )
        lines.append("</viewer_notes>")
    return "\n".join(lines)


def create_agent(*, api_key: str, model: str) -> Agent:
    """Build a single-turn Agno agent backed by a Groq chat model."""
    return Agent(
        model=Groq(
            id=model,
            api_key=api_key,
            max_tokens=GROQ_MAX_TOKENS,
            temperature=GROQ_TEMPERATURE,
        ),
        instructions=SYSTEM_PROMPT,
        markdown=True,
    )


class GroqProvider:
    """Runs one Agno inference with a strict timeout; fails fast."""

    def __init__(
        self,
        *,
        api_key: str = "",
        model: str = "",
        agent: InsightAgent | None = None,
        timeout: float = GROQ_TIMEOUT_SECONDS,
    ) -> None:
        """Configure the agent, or inject one for tests."""
        self._agent = agent or create_agent(api_key=api_key, model=model)
        self._timeout = timeout

    async def generate_insight(self, context: InsightContext) -> SeriesInsight:
        """Request an insight; raise GroqProviderError on any failure."""
        try:
            output = await asyncio.wait_for(
                self._agent.arun(build_prompt(context)),
                timeout=self._timeout,
            )
        except TimeoutError as e:
            raise GroqProviderError("Groq call timed out") from e
        except Exception as e:  # noqa: BLE001 - provider boundary
            raise GroqProviderError("Groq call failed") from e

        content = getattr(output, "content", None)
        text = content.strip() if isinstance(content, str) else ""
        if not text:
            raise GroqProviderError("Empty completion")
        return SeriesInsight(
            text=text,
            highlights=tuple(context.series.genres[:MAX_HIGHLIGHTS]),
            source="llm:groq",
        )
