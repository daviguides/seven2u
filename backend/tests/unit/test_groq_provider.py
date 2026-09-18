import asyncio
from types import SimpleNamespace

import pytest

from app.domain.models import InsightContext
from app.infrastructure.groq_provider import (
    GroqProvider,
    GroqProviderError,
    build_prompt,
)


class FakeAgent:
    def __init__(self, content=None, error=None, delay=0.0):
        self.content = content
        self.error = error
        self.delay = delay
        self.inputs: list[str] = []

    async def arun(self, input: str):
        self.inputs.append(input)
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.error:
            raise self.error
        return SimpleNamespace(content=self.content)


def test_build_prompt_includes_delimited_summary_and_comments(series):
    context = InsightContext(series=series, comments=("great",))

    prompt = build_prompt(context)

    assert "Breaking Bad" in prompt
    assert "<summary>" in prompt
    assert "- great" in prompt


async def test_groq_provider_returns_agent_content(series):
    agent = FakeAgent(content=" Insightful. ")
    provider = GroqProvider(agent=agent)

    insight = await provider.generate_insight(InsightContext(series=series))

    assert insight.text == "Insightful."
    assert insight.source == "llm:groq"
    assert insight.highlights == ("Drama", "Crime", "Thriller")
    assert "Breaking Bad" in agent.inputs[0]


async def test_groq_provider_raises_on_agent_error(series):
    provider = GroqProvider(agent=FakeAgent(error=RuntimeError("down")))

    with pytest.raises(GroqProviderError):
        await provider.generate_insight(InsightContext(series=series))


async def test_groq_provider_raises_on_empty_content(series):
    provider = GroqProvider(agent=FakeAgent(content="   "))

    with pytest.raises(GroqProviderError):
        await provider.generate_insight(InsightContext(series=series))


async def test_groq_provider_raises_on_timeout(series):
    provider = GroqProvider(agent=FakeAgent(content="x", delay=1), timeout=0.01)

    with pytest.raises(GroqProviderError, match="timed out"):
        await provider.generate_insight(InsightContext(series=series))
