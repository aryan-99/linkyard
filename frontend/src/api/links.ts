const BASE = "http://localhost:8000";

export interface LinkResponse {
  id: string;
  url: string;
  title: string | null;
  snippet: string | null;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface LinkDetailResponse extends LinkResponse {
  meta_description: string | null;
}

export interface LinkListResponse {
  items: LinkResponse[];
  pagination: { limit: number; offset: number; total: number };
}

export interface LinkCreate {
  url: string;
  title?: string;
  snippet?: string;
  source: "web" | "extension" | "api";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status}: ${detail}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export function createLink(data: LinkCreate): Promise<LinkDetailResponse> {
  return request<LinkDetailResponse>("/links", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function listLinks(
  limit = 20,
  offset = 0
): Promise<LinkListResponse> {
  return request<LinkListResponse>(
    `/links?limit=${limit}&offset=${offset}`
  );
}

export function deleteLink(id: string): Promise<void> {
  return request<void>(`/links/${id}`, { method: "DELETE" });
}
