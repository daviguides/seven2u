import { ImageOff, Star } from "lucide-react";
import { Link } from "react-router-dom";

import type { Series } from "../api/types";
import { yearOf } from "../lib/utils";
import { GenreChip } from "./GenreChip";

const MAX_CHIPS = 3;

export function SeriesCard({ series }: { series: Series }) {
  const year = yearOf(series.premiered);
  return (
    <Link
      to={`/series/${series.id}`}
      className="focus-ring card group flex flex-col overflow-hidden transition hover:-translate-y-0.5 hover:border-primary/60"
    >
      <div className="relative aspect-[2/3] w-full overflow-hidden bg-elevated">
        {series.image_url ? (
          <img
            src={series.image_url}
            alt={series.name}
            loading="lazy"
            className="h-full w-full object-cover transition duration-300 group-hover:scale-[1.03]"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-text-muted">
            <ImageOff size={28} />
          </div>
        )}
        {series.rating !== null && (
          <span className="absolute right-2 top-2 inline-flex items-center gap-1 rounded-chip bg-bg/80 px-1.5 py-0.5 font-mono text-xs text-primary backdrop-blur">
            <Star size={12} className="fill-primary" />
            {series.rating.toFixed(1)}
          </span>
        )}
      </div>
      <div className="flex flex-1 flex-col gap-2 p-3">
        <div>
          <h3 className="line-clamp-1 font-semibold">{series.name}</h3>
          {year && (
            <p className="font-mono text-xs text-text-muted">{year}</p>
          )}
        </div>
        {series.genres.length > 0 && (
          <div className="mt-auto flex flex-wrap gap-1">
            {series.genres.slice(0, MAX_CHIPS).map((g) => (
              <GenreChip key={g} label={g} />
            ))}
          </div>
        )}
      </div>
    </Link>
  );
}
