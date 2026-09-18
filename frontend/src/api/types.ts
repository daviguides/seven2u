export interface Series {
  id: number;
  name: string;
  summary: string | null;
  genres: string[];
  premiered: string | null;
  status: string | null;
  image_url: string | null;
  rating: number | null;
}

export interface Episode {
  id: number;
  season: number;
  number: number | null;
  name: string;
  summary: string | null;
  airdate: string | null;
  image_url: string | null;
  runtime: number | null;
  watched: boolean;
}

export interface Season {
  number: number;
  episodes: Episode[];
  watched_count: number;
  total: number;
  completion: number;
}

export interface SeriesDetail {
  series: Series;
  seasons: Season[];
  total_episodes: number;
  watched_count: number;
}

export interface WatchedResult {
  episode_id: number;
  series_id: number;
  watched: boolean;
  watched_at: string | null;
}

export interface Comment {
  id: string;
  series_id: number;
  episode_id: number | null;
  content: string;
  created_at: string;
}

export type InsightSource = "llm:huggingface" | "heuristic:fallback";

export interface Insight {
  text: string;
  highlights: string[];
  source: InsightSource;
}
