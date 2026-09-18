import { useCallback, useEffect, useState } from "react";

import { api } from "../../api/client";
import type { SeriesDetail } from "../../api/types";

interface DetailState {
  detail: SeriesDetail | null;
  loading: boolean;
  error: string | null;
}

export function useSeriesDetail(seriesId: number) {
  const [state, setState] = useState<DetailState>({
    detail: null,
    loading: true,
    error: null,
  });
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setState({ detail: null, loading: true, error: null });
    api
      .getSeriesDetail(seriesId, controller.signal)
      .then((detail) => {
        if (!controller.signal.aborted) {
          setState({ detail, loading: false, error: null });
        }
      })
      .catch((e: unknown) => {
        if (controller.signal.aborted) return;
        const message =
          e instanceof Error ? e.message : "Could not load this series";
        setState({ detail: null, loading: false, error: message });
      });
    return () => controller.abort();
  }, [seriesId, reloadKey]);

  const reload = useCallback(() => setReloadKey((k) => k + 1), []);

  const setDetail = useCallback(
    (updater: (current: SeriesDetail) => SeriesDetail) => {
      setState((s) =>
        s.detail ? { ...s, detail: updater(s.detail) } : s,
      );
    },
    [],
  );

  return { ...state, reload, setDetail };
}
