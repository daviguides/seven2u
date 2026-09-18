import { Loader2, Search, X } from "lucide-react";

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  loading: boolean;
}

export function SearchBar({ value, onChange, loading }: SearchBarProps) {
  return (
    <label className="relative block w-full">
      <span className="sr-only">Search series</span>
      <Search
        size={18}
        className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-text-muted"
      />
      <input
        type="search"
        autoFocus
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Search for a series…"
        className="focus-ring w-full rounded-card border border-border bg-surface py-3 pl-11 pr-11 text-base placeholder:text-text-muted transition focus-visible:border-primary"
      />
      <span className="absolute right-4 top-1/2 -translate-y-1/2 text-text-muted">
        {loading ? (
          <Loader2 size={18} className="animate-spin text-primary" />
        ) : value ? (
          <button
            type="button"
            aria-label="Clear search"
            onClick={() => onChange("")}
            className="focus-ring rounded-btn hover:text-text-primary"
          >
            <X size={18} />
          </button>
        ) : null}
      </span>
    </label>
  );
}
