import { useEffect, useRef, useState } from "react";

import { api } from "../../api/client";
import type { Series } from "../../api/types";

const DEBOUNCE_MS = 300;

interface SearchState {
  results: Series[];
  loading: boolean;
  error: string | null;
  searched: boolean;
}

const INITIAL: SearchState = {
  results: [],
  loading: false,
  error: null,
  searched: false,
};

export function useSearch(query: string, reloadKey = 0) {
  const [state, setState] = useState<SearchState>(INITIAL);
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const trimmed = query.trim();
    controllerRef.current?.abort();
    if (!trimmed) {
      setState(INITIAL);
      return;
    }

    const controller = new AbortController();
    controllerRef.current = controller;
    setState((s) => ({ ...s, loading: true, error: null }));

    const timer = window.setTimeout(() => {
      api
        .searchSeries(trimmed, controller.signal)
        .then((results) => {
          if (controller.signal.aborted) return;
          setState({ results, loading: false, error: null, searched: true });
        })
        .catch((e: unknown) => {
          if (controller.signal.aborted) return;
          const message =
            e instanceof Error ? e.message : "Search failed, try again";
          setState({ results: [], loading: false, error: message, searched: true });
        });
    }, DEBOUNCE_MS);

    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [query, reloadKey]);

  return state;
}
