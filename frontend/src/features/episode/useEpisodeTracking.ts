import { useCallback, useState } from "react";

import { api } from "../../api/client";
import type { Episode, SeriesDetail } from "../../api/types";
import { useToast } from "../../components/Toast";

type DetailUpdater = (updater: (d: SeriesDetail) => SeriesDetail) => void;

function applyWatched(
  detail: SeriesDetail,
  episodeId: number,
  watched: boolean,
): SeriesDetail {
  let delta = 0;
  const seasons = detail.seasons.map((season) => {
    const episodes = season.episodes.map((ep) => {
      if (ep.id !== episodeId || ep.watched === watched) return ep;
      delta += watched ? 1 : -1;
      return { ...ep, watched };
    });
    const watched_count = episodes.filter((e) => e.watched).length;
    return {
      ...season,
      episodes,
      watched_count,
      completion: season.total ? watched_count / season.total : 0,
    };
  });
  return { ...detail, seasons, watched_count: detail.watched_count + delta };
}

export function useEpisodeTracking(seriesId: number, setDetail: DetailUpdater) {
  const { notify } = useToast();
  const [pendingIds, setPendingIds] = useState<Set<number>>(new Set());

  const toggleWatched = useCallback(
    async (episode: Episode) => {
      const next = !episode.watched;
      setPendingIds((s) => new Set(s).add(episode.id));
      setDetail((d) => applyWatched(d, episode.id, next));
      try {
        await api.setWatched(seriesId, episode.id, next);
      } catch (e) {
        setDetail((d) => applyWatched(d, episode.id, episode.watched));
        notify(e instanceof Error ? e.message : "Could not update episode");
      } finally {
        setPendingIds((s) => {
          const copy = new Set(s);
          copy.delete(episode.id);
          return copy;
        });
      }
    },
    [seriesId, setDetail, notify],
  );

  return { pendingIds, toggleWatched };
}
