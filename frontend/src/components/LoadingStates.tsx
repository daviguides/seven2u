import { RefreshCw, SearchX, Tv } from "lucide-react";

import { cn } from "../lib/utils";

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      aria-hidden
      className={cn("animate-pulse rounded-btn bg-elevated", className)}
    />
  );
}

export function SeriesCardSkeleton() {
  return (
    <div className="card overflow-hidden">
      <Skeleton className="aspect-[2/3] w-full rounded-none" />
      <div className="space-y-2 p-3">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/3" />
      </div>
    </div>
  );
}

export function SeriesDetailSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-6 sm:flex-row">
        <Skeleton className="aspect-[2/3] w-full max-w-[220px] rounded-poster" />
        <div className="flex-1 space-y-3">
          <Skeleton className="h-8 w-2/3" />
          <Skeleton className="h-4 w-1/4" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
        </div>
      </div>
      <Skeleton className="h-14 w-full" />
      <Skeleton className="h-14 w-full" />
    </div>
  );
}

interface EmptyStateProps {
  icon?: "search" | "tv";
  title: string;
  hint?: string;
}

export function EmptyState({ icon = "search", title, hint }: EmptyStateProps) {
  const Icon = icon === "tv" ? Tv : SearchX;
  return (
    <div className="flex flex-col items-center gap-2 py-16 text-center">
      <Icon size={36} className="text-text-muted" />
      <p className="font-semibold">{title}</p>
      {hint && <p className="text-sm text-text-secondary">{hint}</p>}
    </div>
  );
}

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="card flex flex-col items-center gap-3 border-red-500/40 p-6 text-center">
      <p className="text-sm text-text-secondary">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="focus-ring inline-flex items-center gap-2 rounded-btn bg-primary px-3 py-1.5 text-sm font-semibold text-bg hover:bg-primary-hover transition"
        >
          <RefreshCw size={14} /> Retry
        </button>
      )}
    </div>
  );
}
