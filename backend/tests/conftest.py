"""Shared fixtures."""

import pytest

from tests.fakes import (
    FakeCatalog,
    FakeCommentRepository,
    FakeWatchedRepository,
    make_episode,
    make_series,
)


@pytest.fixture
def series():
    return make_series()


@pytest.fixture
def episodes():
    return [
        make_episode(11, 1, 1),
        make_episode(12, 1, 2),
        make_episode(21, 2, 1),
        make_episode(22, 2, 2),
        make_episode(23, 2, 3),
    ]


@pytest.fixture
def catalog(series, episodes):
    return FakeCatalog(series=[series], episodes={series.id: episodes})


@pytest.fixture
def watched_repo():
    return FakeWatchedRepository()


@pytest.fixture
def comment_repo():
    return FakeCommentRepository()
