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

import { request } from "./client";

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
