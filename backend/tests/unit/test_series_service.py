import pytest

from app.domain.errors import NotFoundError, ValidationError
from app.services.series_service import MAX_QUERY_LENGTH, SeriesService


@pytest.fixture
def service(catalog, watched_repo):
    return SeriesService(catalog=catalog, watched_repo=watched_repo)


async def test_series_service_search_trims_and_delegates(service, catalog):
    results = await service.search("  breaking ")

    assert catalog.search_calls == ["breaking"]
    assert [s.name for s in results] == ["Breaking Bad"]


async def test_series_service_search_rejects_blank_query(service):
    with pytest.raises(ValidationError):
        await service.search("   ")


async def test_series_service_search_rejects_long_query(service):
    with pytest.raises(ValidationError):
        await service.search("x" * (MAX_QUERY_LENGTH + 1))


async def test_series_service_details_groups_and_hydrates_watched(
    service, watched_repo, series
):
    await watched_repo.set_watched(
        series_id=series.id, episode_id=11, watched=True
    )

    detail = await service.get_details(series.id)

    assert detail.series.name == "Breaking Bad"
    assert [s.number for s in detail.seasons] == [1, 2]
    assert detail.seasons[0].watched_ids == frozenset({11})
    assert detail.total_episodes == 5
    assert detail.watched_count == 1


async def test_series_service_details_unknown_series_raises(service):
    with pytest.raises(NotFoundError):
        await service.get_details(999)
