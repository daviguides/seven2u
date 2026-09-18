import pytest

from app.domain.errors import NotFoundError
from app.services.tracking_service import TrackingService


@pytest.fixture
def service(catalog, watched_repo):
    return TrackingService(catalog=catalog, watched_repo=watched_repo)


async def test_tracking_service_marks_episode_watched(service, series):
    marker = await service.set_watched(
        series_id=series.id, episode_id=11, watched=True
    )

    assert marker is not None
    assert await service.watched_ids(series.id) == frozenset({11})


async def test_tracking_service_set_watched_twice_is_idempotent(
    service, series
):
    first = await service.set_watched(
        series_id=series.id, episode_id=11, watched=True
    )
    second = await service.set_watched(
        series_id=series.id, episode_id=11, watched=True
    )

    assert first == second
    assert await service.watched_ids(series.id) == frozenset({11})


async def test_tracking_service_unwatch_removes_marker(service, series):
    await service.set_watched(series_id=series.id, episode_id=11, watched=True)

    result = await service.set_watched(
        series_id=series.id, episode_id=11, watched=False
    )

    assert result is None
    assert await service.watched_ids(series.id) == frozenset()


async def test_tracking_service_unwatch_absent_is_noop(service, series):
    result = await service.set_watched(
        series_id=series.id, episode_id=11, watched=False
    )

    assert result is None


async def test_tracking_service_rejects_episode_outside_series(service, series):
    with pytest.raises(NotFoundError):
        await service.set_watched(
            series_id=series.id, episode_id=999, watched=True
        )


async def test_tracking_service_rejects_unknown_series(service):
    with pytest.raises(NotFoundError):
        await service.set_watched(series_id=404, episode_id=11, watched=True)
