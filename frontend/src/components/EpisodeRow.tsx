import { ChevronDown, Eye, EyeOff, MessageCircle, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";

import type { Episode } from "../api/types";
import { cn, episodeCode } from "../lib/utils";
import { CommentSection } from "./CommentSection";
import { InsightCard } from "./InsightCard";

interface EpisodeRowProps {
  seriesId: number;
  episode: Episode;
  pending: boolean;
  onToggleWatched: (episode: Episode) => void;
}

type Panel = "comments" | "insight" | null;

export function EpisodeRow({
  seriesId,
  episode,
  pending,
  onToggleWatched,
}: EpisodeRowProps) {
  const [panel, setPanel] = useState<Panel>(null);
  const [flash, setFlash] = useState(false);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (!episode.watched) return;
    setFlash(true);
    const t = window.setTimeout(() => setFlash(false), 600);
    return () => window.clearTimeout(t);
  }, [episode.watched]);

  const togglePanel = (next: Panel) =>
    setPanel((current) => (current === next ? null : next));

  return (
    <li
      className={cn(
        "border-t border-border first:border-t-0",
        flash && "flash-success",
      )}
    >
      <div className="flex items-center gap-3 px-3 py-2.5 sm:px-4">
        <button
          type="button"
          disabled={pending}
          aria-pressed={episode.watched}
          aria-label={episode.watched ? "Mark as unwatched" : "Mark as watched"}
          onClick={() => onToggleWatched(episode)}
          className={cn(
            "focus-ring shrink-0 rounded-btn p-1.5 transition disabled:opacity-50",
            episode.watched
              ? "text-success hover:bg-success/10"
              : "text-text-muted hover:bg-elevated hover:text-text-primary",
          )}
        >
          {episode.watched ? <Eye size={18} /> : <EyeOff size={18} />}
        </button>

        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="focus-ring flex min-w-0 flex-1 items-center gap-3 rounded-btn text-left"
        >
          <span className="shrink-0 font-mono text-xs text-text-muted">
            {episodeCode(episode.season, episode.number)}
          </span>
          <span
            className={cn(
              "truncate text-sm",
              episode.watched ? "text-text-secondary" : "text-text-primary",
            )}
          >
            {episode.name}
          </span>
          {episode.airdate && (
            <span className="ml-auto hidden shrink-0 font-mono text-xs text-text-muted sm:inline">
              {episode.airdate}
            </span>
          )}
          <ChevronDown
            size={14}
            className={cn(
              "shrink-0 text-text-muted transition",
              expanded && "rotate-180",
            )}
          />
        </button>

        <div className="flex shrink-0 items-center gap-1">
          <button
            type="button"
            aria-label="Comments"
            aria-pressed={panel === "comments"}
            onClick={() => togglePanel("comments")}
            className={cn(
              "focus-ring rounded-btn p-1.5 transition hover:bg-elevated",
              panel === "comments" ? "text-primary" : "text-text-muted",
            )}
          >
            <MessageCircle size={16} />
          </button>
          <button
            type="button"
            aria-label="AI insight"
            aria-pressed={panel === "insight"}
            onClick={() => togglePanel("insight")}
            className={cn(
              "focus-ring rounded-btn p-1.5 transition hover:bg-elevated",
              panel === "insight" ? "text-accent" : "text-text-muted",
            )}
          >
            <Sparkles size={16} />
          </button>
        </div>
      </div>

      {expanded && episode.summary && (
        <p className="px-4 pb-3 pl-12 text-sm text-text-secondary sm:pl-14">
          {episode.summary}
        </p>
      )}

      {panel === "insight" && (
        <div className="px-3 pb-3 sm:px-4">
          <InsightCard
            key={`ep-${episode.id}`}
            seriesId={seriesId}
            episodeId={episode.id}
            compact
          />
        </div>
      )}
      {panel === "comments" && (
        <div className="px-3 pb-3 sm:px-4">
          <CommentSection seriesId={seriesId} episodeId={episode.id} compact />
        </div>
      )}
    </li>
  );
}
