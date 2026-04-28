const BASE = "http://localhost:8000";

export interface AppSettings {
  embedding_provider: string;
  has_openai_key: boolean;
}

export interface SettingsUpdate {
  embedding_provider?: string;
  openai_api_key?: string | null;
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
