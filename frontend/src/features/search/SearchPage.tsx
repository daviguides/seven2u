import { useState } from "react";
import { useSearchParams } from "react-router-dom";

import {
  EmptyState,
  ErrorState,
  SeriesCardSkeleton,
} from "../../components/LoadingStates";
import { SearchBar } from "../../components/SearchBar";
import { SeriesCard } from "../../components/SeriesCard";
import { useSearch } from "./useSearch";

const SKELETON_COUNT = 8;

export function SearchPage() {
  const [params, setParams] = useSearchParams();
  const query = params.get("q") ?? "";
  const [reloadKey, setReloadKey] = useState(0);
  const { results, loading, error, searched } = useSearch(query, reloadKey);

  const setQuery = (value: string) => {
    setParams(value ? { q: value } : {}, { replace: true });
  };

  return (
    <div className="space-y-8">
      <section className="mx-auto max-w-2xl space-y-3 pt-4 text-center sm:pt-10">
        <h1 className="text-2xl font-bold sm:text-4xl">
          Never lose where you stopped.
        </h1>
        <p className="text-text-secondary">
          Find a series, track episodes, and know what to expect before you
          press play.
        </p>
        <SearchBar value={query} onChange={setQuery} loading={loading} />
      </section>

      <section aria-live="polite">
        {!query.trim() ? (
          <EmptyState
            icon="tv"
            title="Start by searching for a series"
            hint='Try "Breaking Bad", "The Office" or "Dark".'
          />
        ) : error ? (
          <ErrorState
            message={error}
            onRetry={() => setReloadKey((k) => k + 1)}
          />
        ) : loading && results.length === 0 ? (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {Array.from({ length: SKELETON_COUNT }).map((_, i) => (
              <SeriesCardSkeleton key={i} />
            ))}
          </div>
        ) : searched && results.length === 0 ? (
          <EmptyState
            title="No results found"
            hint="Check the spelling or try a broader title."
          />
        ) : (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {results.map((s) => (
              <SeriesCard key={s.id} series={s} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
