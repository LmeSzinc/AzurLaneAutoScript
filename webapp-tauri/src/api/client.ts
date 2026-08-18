import type { ArgSchema, MenuSchema, Status } from "./types";

/**
 * Base URL of the python backend.
 * Empty means same origin (production: served by the backend itself,
 * or the Tauri shell which loads the page from the backend).
 * Overridable via VITE_API_BASE for the vite dev server.
 */
const BASE = import.meta.env.VITE_API_BASE ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    throw new Error(`${path} -> ${res.status}`);
  }
  return (await res.json()) as T;
}

export const api = {
  status: () => request<Status>("/status"),

  schema: (mod = "alas") => request<{ menu: MenuSchema; args: ArgSchema }>(`/schema/${mod}`),

  config: (name: string) => request<Record<string, unknown>>(`/config/${name}`),

  saveConfig: (name: string, values: Record<string, unknown>) =>
    request<{ valid: string[]; invalid: string[] }>(`/config/${name}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value: values }),
    }),

  i18n: (lang: string) => request<Record<string, string>>(`/i18n/${lang}`),

  setLanguage: (language: string) =>
    request<{ language: string }>("/language", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ language }),
    }),

  setTheme: (theme: string) =>
    request<{ theme: string }>("/theme", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ theme }),
    }),

  run: (instance: string, func?: string) =>
    request<{ ok: boolean; error?: string }>("/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ instance, func }),
    }),

  stop: (instance: string) =>
    request<{ ok: boolean }>("/stop", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ instance }),
    }),

  newInstance: (name: string, origin?: string) =>
    request<{ ok: boolean; error?: string }>("/instance/new", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, origin }),
    }),

  deleteInstance: (name: string) =>
    request<{ ok: boolean; error?: string }>("/instance/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    }),

  importConfig: (name: string, config: Record<string, unknown>) =>
    request<{ ok: boolean }>(`/config/${name}/import`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ config }),
    }),

  updateStatus: () => request<{ state: string; current: { sha: string; message: string } | null }>("/update/status"),

  updateHistory: () =>
    request<{
      local: string[] | null;
      upstream: string[] | null;
      history: string[][];
    }>("/update/history"),

  configs: () => request<{ name: string; modified: string }[]>("/configs"),

  updateCheck: () => request<{ ok: boolean }>("/update/check", { method: "POST" }),

  updateRun: () => request<{ ok: boolean }>("/update/run", { method: "POST" }),

  remoteStatus: () => request<{ alive: boolean; state: string; entry_point: string }>("/remote/status"),

  remoteStart: () => request<{ ok: boolean }>("/remote/start", { method: "POST" }),

  remoteStop: () => request<{ ok: boolean }>("/remote/stop", { method: "POST" }),

  scheduler: (name: string) =>
    request<{
      alive: boolean;
      running: { command: string; next_run: string }[];
      pending: { command: string; next_run: string }[];
      waiting: { command: string; next_run: string }[];
    }>(`/scheduler/${name}`),
};

export type { Status };
