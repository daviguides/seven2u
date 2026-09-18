export function GenreChip({ label }: { label: string }) {
  return (
    <span className="rounded-chip border border-border bg-elevated px-2 py-0.5 text-xs text-text-secondary">
      {label}
    </span>
  );
}
