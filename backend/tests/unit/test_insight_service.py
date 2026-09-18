import asyncio

import pytest

from app.domain.errors import NotFoundError
from app.domain.models import InsightContext, SeriesInsight
from app.infrastructure.heuristic_provider import HeuristicTemplateProvider
from app.services.insight_service import InsightService
from tests.fakes import StubProvider


class SlowProvider:
    async def generate_insight(self, context: InsightContext) -> SeriesInsight:
        await asyncio.wait_for(asyncio.sleep(10), timeout=0.01)
        raise AssertionError("unreachable")


def build(catalog, watched_repo, comment_repo, primary):
    return InsightService(
        catalog=catalog,
        watched_repo=watched_repo,
        comment_repo=comment_repo,
        primary=primary,
        fallback=HeuristicTemplateProvider(),
    )


async def test_insight_service_uses_primary_when_it_succeeds(
    catalog, watched_repo, comment_repo, series
):
    primary = StubProvider(text="llm text")
    service = build(catalog, watched_repo, comment_repo, primary)

    insight = await service.for_series(series.id)

    assert insight.text == "llm text"
    assert insight.source == "llm:groq"


async def test_insight_service_falls_back_when_primary_raises(
    catalog, watched_repo, comment_repo, series
):
    primary = StubProvider(error=RuntimeError("boom"))
    service = build(catalog, watched_repo, comment_repo, primary)

    insight = await service.for_series(series.id)

    assert insight.source == "heuristic:fallback"
    assert "Breaking Bad" in insight.text


async def test_insight_service_falls_back_on_timeout(
    catalog, watched_repo, comment_repo, series
):
    service = build(catalog, watched_repo, comment_repo, SlowProvider())

    insight = await service.for_series(series.id)

    assert insight.source == "heuristic:fallback"


async def test_insight_service_without_primary_uses_fallback(
    catalog, watched_repo, comment_repo, series
):
    service = build(catalog, watched_repo, comment_repo, None)

    insight = await service.for_series(series.id)

    assert insight.source == "heuristic:fallback"
    assert insight.highlights == ("Drama", "Crime", "Thriller")


async def test_insight_service_passes_progress_and_comments_to_provider(
    catalog, watched_repo, comment_repo, series
):
    await watched_repo.set_watched(
        series_id=series.id, episode_id=11, watched=True
    )
    await comment_repo.add(series_id=series.id, episode_id=None, content="wow")
    await comment_repo.add(series_id=series.id, episode_id=11, content="ep")
    primary = StubProvider()
    service = build(catalog, watched_repo, comment_repo, primary)

    await service.for_series(series.id)
    await service.for_episode(series_id=series.id, episode_id=11)

    series_ctx, episode_ctx = primary.calls
    assert series_ctx.total_episodes == 5
    assert series_ctx.watched_count == 1
    assert series_ctx.comments == ("wow", "ep")
    assert episode_ctx.episode is not None
    assert episode_ctx.episode.id == 11
    assert episode_ctx.comments == ("ep",)


async def test_insight_service_unknown_episode_raises(
    catalog, watched_repo, comment_repo, series
):
    service = build(catalog, watched_repo, comment_repo, None)

    with pytest.raises(NotFoundError):
        await service.for_episode(series_id=series.id, episode_id=999)


async def test_heuristic_provider_reflects_progress(series, episodes):
    provider = HeuristicTemplateProvider()
    context = InsightContext(
        series=series, total_episodes=4, watched_count=3, comments=("a",)
    )

    insight = await provider.generate_insight(context)

    assert "final stretch" in insight.text
    assert "1 note" in insight.text
    assert "character-driven" in insight.text
