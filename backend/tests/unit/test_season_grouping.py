from app.domain.progress import group_by_season
from tests.fakes import make_episode


def test_group_by_season_empty_returns_no_seasons():
    assert group_by_season([]) == ()


def test_group_by_season_sorts_seasons_ascending():
    episodes = [
        make_episode(3, 3, 1),
        make_episode(1, 1, 1),
        make_episode(2, 2, 1),
    ]

    seasons = group_by_season(episodes)

    assert [s.number for s in seasons] == [1, 2, 3]


def test_group_by_season_orders_episodes_and_puts_specials_last():
    episodes = [
        make_episode(3, 1, None),
        make_episode(2, 1, 2),
        make_episode(1, 1, 1),
    ]

    seasons = group_by_season(episodes)

    assert [ep.id for ep in seasons[0].episodes] == [1, 2, 3]


def test_group_by_season_ignores_foreign_watched_ids():
    episodes = [make_episode(1, 1, 1), make_episode(2, 1, 2)]

    seasons = group_by_season(episodes, frozenset({1, 999}))

    assert seasons[0].watched_ids == frozenset({1})
    assert seasons[0].completion == 0.5


def test_season_completion_all_watched_is_one():
    episodes = [make_episode(1, 1, 1), make_episode(2, 1, 2)]

    seasons = group_by_season(episodes, frozenset({1, 2}))

    assert seasons[0].completion == 1.0
    assert seasons[0].watched_count == 2


def test_group_by_season_keeps_specials_as_season_zero():
    episodes = [make_episode(9, 0, 1), make_episode(1, 1, 1)]

    seasons = group_by_season(episodes)

    assert seasons[0].number == 0
