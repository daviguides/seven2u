"""HuggingFace Inference API implementation of InsightProvider."""

from typing import Any

import httpx

from app.domain.models import InsightContext, SeriesInsight

HF_ROUTER_URL = "https://router.huggingface.co/v1/chat/completions"
HF_TIMEOUT_SECONDS = 2.5
HF_MAX_TOKENS = 220
HF_TEMPERATURE = 0.7
MAX_SUMMARY_CHARS = 800
MAX_COMMENTS_IN_PROMPT = 5

SYSTEM_PROMPT = (
    "You are a thoughtful TV critic. Write a spoiler-free insight of at "
    "most 120 words describing the tone, themes, pacing and what kind of "
    "viewer will enjoy it. Never reveal plot twists or endings. Reply with "
    "plain prose, no headings, no bullet points."
)


class HuggingFaceProviderError(Exception):
    """Raised when the HuggingFace API returns an unusable response."""


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


class HuggingFaceProvider:
    """Calls a chat-completion model with a strict timeout; fails fast."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        client: httpx.AsyncClient | None = None,
        url: str = HF_ROUTER_URL,
    ) -> None:
        """Configure credentials, model and optional client for tests."""
        self._model = model
        self._url = url
        self._headers = {"Authorization": f"Bearer {api_key}"}
        self._client = client or httpx.AsyncClient(
            timeout=HF_TIMEOUT_SECONDS,
        )

    async def aclose(self) -> None:
        """Release the HTTP client."""
        await self._client.aclose()

    async def generate_insight(self, context: InsightContext) -> SeriesInsight:
        """Request an insight; raise on timeout, HTTP or parse errors."""
        payload: dict[str, Any] = {
            "model": self._model,
            "max_tokens": HF_MAX_TOKENS,
            "temperature": HF_TEMPERATURE,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_prompt(context)},
            ],
        }
        try:
            response = await self._client.post(
                self._url,
                json=payload,
                headers=self._headers,
                timeout=HF_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()
            text = data["choices"][0]["message"]["content"].strip()
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as e:
            raise HuggingFaceProviderError("HuggingFace call failed") from e
        if not text:
            raise HuggingFaceProviderError("Empty completion")
        return SeriesInsight(
            text=text,
            highlights=tuple(context.series.genres[:3]),
            source="llm:huggingface",
        )
