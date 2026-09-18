import { ArrowLeft, ImageOff, Star } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { CommentSection } from "../../components/CommentSection";
import { GenreChip } from "../../components/GenreChip";
import { InsightCard } from "../../components/InsightCard";
import {
  EmptyState,
  ErrorState,
  SeriesDetailSkeleton,
} from "../../components/LoadingStates";
import { SeasonAccordion } from "../../components/SeasonAccordion";
import { yearOf } from "../../lib/utils";
import { useEpisodeTracking } from "../episode/useEpisodeTracking";
import { useSeriesDetail } from "./useSeriesDetail";

export function SeriesDetailPage() {
  const { seriesId: raw } = useParams();
  const seriesId = Number(raw);
  const { detail, loading, error, reload, setDetail } =
    useSeriesDetail(seriesId);
  const { pendingIds, toggleWatched } = useEpisodeTracking(
    seriesId,
    setDetail,
  );

  const back = (
    <Link
      to="/"
      className="focus-ring inline-flex items-center gap-1.5 rounded-btn text-sm text-text-secondary hover:text-text-primary transition"
    >
      <ArrowLeft size={16} /> Back to search
    </Link>
  );

  if (loading) {
    return (
      <div className="space-y-6">
        {back}
        <SeriesDetailSkeleton />
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="space-y-6">
        {back}
        <ErrorState message={error ?? "Series not found"} onRetry={reload} />
      </div>
    );
  }

  const { series, seasons } = detail;
  const year = yearOf(series.premiered);
  const overall = detail.total_episodes
    ? Math.round((detail.watched_count / detail.total_episodes) * 100)
    : 0;
  const firstIncomplete = seasons.findIndex((s) => s.completion < 1);
  const openIndex = firstIncomplete === -1 ? 0 : firstIncomplete;

  return (
    <div className="space-y-8">
      {back}

      <section className="flex flex-col gap-6 sm:flex-row">
        <div className="w-full max-w-[220px] shrink-0 self-start overflow-hidden rounded-poster bg-elevated">
          {series.image_url ? (
            <img
              src={series.image_url}
              alt={series.name}
              className="aspect-[2/3] w-full object-cover"
            />
          ) : (
            <div className="flex aspect-[2/3] items-center justify-center text-text-muted">
              <ImageOff size={32} />
            </div>
          )}
        </div>
        <div className="min-w-0 flex-1 space-y-3">
          <div>
            <h1 className="text-2xl font-bold sm:text-3xl">{series.name}</h1>
            <p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-xs text-text-muted">
              {year && <span>{year}</span>}
              {series.status && <span>{series.status}</span>}
              {series.rating !== null && (
                <span className="inline-flex items-center gap-1 text-primary">
                  <Star size={12} className="fill-primary" />
                  {series.rating.toFixed(1)}
                </span>
              )}
              <span>
                {detail.total_episodes} episodes · {seasons.length}{" "}
                {seasons.length === 1 ? "season" : "seasons"}
              </span>
            </p>
          </div>
          {series.genres.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {series.genres.map((g) => (
                <GenreChip key={g} label={g} />
              ))}
            </div>
          )}
          {series.summary && (
            <p className="text-sm leading-relaxed text-text-secondary">
              {series.summary}
            </p>
          )}
          <div className="space-y-1 pt-1">
            <div className="flex justify-between font-mono text-xs text-text-secondary">
              <span>Your progress</span>
              <span>
                {detail.watched_count}/{detail.total_episodes} · {overall}%
              </span>
            </div>
            <div
              role="progressbar"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={overall}
              className="h-2 w-full overflow-hidden rounded-full bg-elevated"
            >
              <div
                className={`h-full rounded-full transition-all duration-300 ${overall === 100 ? "bg-success" : "bg-primary"}`}
                style={{ width: `${overall}%` }}
              />
            </div>
          </div>
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <div className="space-y-3">
          <h2 className="text-lg font-semibold">Episodes</h2>
          {seasons.length === 0 ? (
            <EmptyState icon="tv" title="No episodes listed yet" />
          ) : (
            seasons.map((season, i) => (
              <SeasonAccordion
                key={season.number}
                seriesId={series.id}
                season={season}
                defaultOpen={i === openIndex}
                pendingIds={pendingIds}
                onToggleWatched={toggleWatched}
              />
            ))
          )}
        </div>
        <aside className="space-y-4 lg:sticky lg:top-20 lg:self-start">
          <InsightCard key={`series-${series.id}`} seriesId={series.id} />
          <CommentSection seriesId={series.id} />
        </aside>
      </div>
    </div>
  );
}
