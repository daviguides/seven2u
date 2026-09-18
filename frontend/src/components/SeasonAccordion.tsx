import { ChevronDown } from "lucide-react";
import { useState } from "react";

import type { Episode, Season } from "../api/types";
import { cn } from "../lib/utils";
import { EpisodeRow } from "./EpisodeRow";

interface SeasonAccordionProps {
  seriesId: number;
  season: Season;
  defaultOpen: boolean;
  pendingIds: Set<number>;
  onToggleWatched: (episode: Episode) => void;
}

export function SeasonAccordion({
  seriesId,
  season,
  defaultOpen,
  pendingIds,
  onToggleWatched,
}: SeasonAccordionProps) {
  const [open, setOpen] = useState(defaultOpen);
  const percent = Math.round(season.completion * 100);
  const label = season.number === 0 ? "Specials" : `Season ${season.number}`;
  const panelId = `season-${season.number}`;

  return (
    <section className="card overflow-hidden">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((v) => !v)}
        className="focus-ring flex w-full items-center gap-3 px-4 py-3 text-left transition hover:bg-elevated/60"
      >
        <ChevronDown
          size={18}
          className={cn(
            "shrink-0 text-text-muted transition duration-200",
            open && "rotate-180",
          )}
        />
        <span className="font-semibold">{label}</span>
        <span className="font-mono text-xs text-text-muted">
          {season.watched_count}/{season.total}
        </span>
        <span className="ml-auto flex items-center gap-2">
          <span
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={percent}
            aria-label={`${label} progress`}
            className="h-1.5 w-20 overflow-hidden rounded-full bg-elevated sm:w-32"
          >
            <span
              className={cn(
                "block h-full rounded-full transition-all duration-300",
                percent === 100 ? "bg-success" : "bg-primary",
              )}
              style={{ width: `${percent}%` }}
            />
          </span>
          <span className="w-9 text-right font-mono text-xs text-text-secondary">
            {percent}%
          </span>
        </span>
      </button>
      {open && (
        <ul id={panelId} className="border-t border-border">
          {season.episodes.map((ep) => (
            <EpisodeRow
              key={ep.id}
              seriesId={seriesId}
              episode={ep}
              pending={pendingIds.has(ep.id)}
              onToggleWatched={onToggleWatched}
            />
          ))}
        </ul>
      )}
    </section>
  );
}
