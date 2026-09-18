import type {
  Comment,
  Insight,
  Series,
  SeriesDetail,
  WatchedResult,
} from "./types";

const API_PREFIX = "/api/v1";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(`${API_PREFIX}${path}`, {
    ...init,
    signal,
    headers: { "Content-Type": "application/json", ...init.headers },
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // non-JSON error body
    }
    throw new ApiError(response.status, detail);
  }
  return (await response.json()) as T;
}

export const api = {
  searchSeries: (query: string, signal?: AbortSignal) =>
    request<Series[]>(
      `/series/search?q=${encodeURIComponent(query)}`,
      {},
      signal,
    ),

  getSeriesDetail: (seriesId: number, signal?: AbortSignal) =>
    request<SeriesDetail>(`/series/${seriesId}`, {}, signal),

  setWatched: (seriesId: number, episodeId: number, watched: boolean) =>
    request<WatchedResult>(`/episodes/${episodeId}/watched`, {
      method: "PUT",
      body: JSON.stringify({ series_id: seriesId, watched }),
    }),

  listComments: (seriesId: number, episodeId?: number) =>
    request<Comment[]>(
      `/series/${seriesId}/comments${episodeId ? `?episode_id=${episodeId}` : ""}`,
    ),

  addComment: (seriesId: number, content: string, episodeId?: number) =>
    request<Comment>(
      `/series/${seriesId}/comments${episodeId ? `?episode_id=${episodeId}` : ""}`,
      { method: "POST", body: JSON.stringify({ content }) },
    ),

  seriesInsight: (seriesId: number) =>
    request<Insight>(`/series/${seriesId}/insights`),

  episodeInsight: (seriesId: number, episodeId: number) =>
    request<Insight>(`/series/${seriesId}/insights/episodes/${episodeId}`),
};
