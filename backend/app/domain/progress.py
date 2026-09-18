"""Pure rules for grouping episodes into seasons."""

from collections import defaultdict

from app.domain.models import Episode, Season


def group_by_season(
    episodes: list[Episode],
    watched_ids: frozenset[int] = frozenset(),
) -> tuple[Season, ...]:
    """Group episodes by season number, sorted ascending.

    Episodes inside a season are ordered by episode number; episodes
    without a number (specials) sort last.

    Args:
        episodes: Flat list of episodes for one series.
        watched_ids: Episode ids already marked as watched.

    Returns:
        Seasons in ascending order, each with its watched subset.
    """
    buckets: dict[int, list[Episode]] = defaultdict(list)
    for episode in episodes:
        buckets[episode.season].append(episode)

    seasons: list[Season] = []
    for number in sorted(buckets):
        ordered = sorted(
            buckets[number],
            key=lambda ep: (ep.number is None, ep.number or 0, ep.id),
        )
        season_watched = frozenset(
            ep.id for ep in ordered if ep.id in watched_ids
        )
        seasons.append(
            Season(
                number=number,
                episodes=tuple(ordered),
                watched_ids=season_watched,
            ),
        )
    return tuple(seasons)
