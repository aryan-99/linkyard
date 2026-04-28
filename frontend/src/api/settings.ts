import { request } from "./client";

export interface AppSettings {
  embedding_provider: string;
  has_openai_key: boolean;
}

export interface SettingsUpdate {
  embedding_provider?: string;
  openai_api_key?: string | null;
}

export function getSettings(): Promise<AppSettings> {
  return request<AppSettings>("/settings");
}

export function updateSettings(update: SettingsUpdate): Promise<AppSettings> {
  return request<AppSettings>("/settings", {
    method: "PUT",
    body: JSON.stringify(update),
  });
}

export function triggerReembed(): Promise<{ reembedded: number }> {
  return request<{ reembedded: number }>("/settings/reembed", {
    method: "POST",
  });
}
