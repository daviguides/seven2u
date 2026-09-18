import httpx
import pytest

from app.domain.models import InsightContext
from app.infrastructure.huggingface_provider import (
    HuggingFaceProvider,
    HuggingFaceProviderError,
    build_prompt,
)


def provider_with(handler):
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return HuggingFaceProvider(api_key="k", model="m", client=client)


def test_build_prompt_includes_delimited_summary_and_comments(series):
    context = InsightContext(series=series, comments=("great",))

    prompt = build_prompt(context)

    assert "Breaking Bad" in prompt
    assert "<summary>" in prompt
    assert "- great" in prompt


async def test_huggingface_provider_parses_completion(series):
    def handler(request):
        assert request.headers["authorization"] == "Bearer k"
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": " Insightful. "}}]},
        )

    provider = provider_with(handler)

    insight = await provider.generate_insight(InsightContext(series=series))

    assert insight.text == "Insightful."
    assert insight.source == "llm:huggingface"


async def test_huggingface_provider_raises_on_http_error(series):
    provider = provider_with(lambda r: httpx.Response(503))

    with pytest.raises(HuggingFaceProviderError):
        await provider.generate_insight(InsightContext(series=series))


async def test_huggingface_provider_raises_on_malformed_json(series):
    provider = provider_with(lambda r: httpx.Response(200, json={"x": 1}))

    with pytest.raises(HuggingFaceProviderError):
        await provider.generate_insight(InsightContext(series=series))


async def test_huggingface_provider_raises_on_timeout(series):
    def handler(request):
        raise httpx.ReadTimeout("slow")

    provider = provider_with(handler)

    with pytest.raises(HuggingFaceProviderError):
        await provider.generate_insight(InsightContext(series=series))
