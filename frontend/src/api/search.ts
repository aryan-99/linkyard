import { LinkResponse } from "./links";

const BASE = "http://localhost:8000";

export interface SearchResultItem extends LinkResponse {
  score: number;
}

export interface SearchResultsResponse {
  items: SearchResultItem[];
  pagination: { limit: number; offset: number; total: number };
}

async function request<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export function searchLinks(
  q: string,
  limit = 20,
  offset = 0
): Promise<SearchResultsResponse> {
  return request<SearchResultsResponse>(
    `/links/search?q=${encodeURIComponent(q)}&limit=${limit}&offset=${offset}`
  );
}
