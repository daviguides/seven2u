export function cn(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

export function yearOf(date: string | null): string | null {
  return date ? date.slice(0, 4) : null;
}

export function episodeCode(season: number, number: number | null): string {
  const s = String(season).padStart(2, "0");
  const e = number === null ? "SP" : String(number).padStart(2, "0");
  return `S${s}E${e}`;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}
