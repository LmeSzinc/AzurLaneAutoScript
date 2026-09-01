import { api } from "./client";
import type { SchedulerSnapshot, SseLog, Status } from "./types";

const BASE = import.meta.env.VITE_API_BASE ?? "";

export const status = $state<Status>({
  instances: [],
  theme: "dark",
  language: "zh-CN",
});

/** WS connection state (wrapped so the property may be reassigned). */
export const connState = $state<{ connected: boolean }>({ connected: false });

/** Per-instance log buffer, newest entries last. */
export const logs = $state<Record<string, string[]>>({});

/** Per-instance live scheduler snapshot pushed by the bot process. */
export const schedulers = $state<Record<string, SchedulerSnapshot>>({});

/** Shared menu collapse state so it survives page navigation. */
export const collapsedGroups = $state<Record<string, boolean>>({});

/** Explicit page title set by pages (e.g. the develop sub pages). */
export const titleState = $state<{ value: string }>({ value: "" });

/**
 * Instance selected in the aside. Persists across page navigation so the
 * overview/settings always follow the instance the user clicked, not just
 * the first configured one.
 */
export const activeInstance = $state<{ name: string }>({ name: "" });

export function selectInstance(name: string) {
  activeInstance.name = name;
}

/** Resolve the effective instance: the selected one, falling back to the
 *  first configured instance (or "alas") while the selection is empty or
 *  the selected instance no longer exists (deleted/renamed). */
export function currentInstance(): string {
  const name = activeInstance.name;
  if (name && status.instances.some((i) => i.name === name)) {
    return name;
  }
  return status.instances[0]?.name ?? "alas";
}

export async function refreshStatus() {
  Object.assign(status, await api.status());
  // Keep the selection valid after instance creation/deletion/rename.
  if (activeInstance.name && !status.instances.some((i) => i.name === activeInstance.name)) {
    activeInstance.name = "";
  }
}

let es: EventSource | null = null;
let reconnectTimer: number | undefined;

// PROBE: temporary instrumentation (revert with the probe commit).
// 30-second summary of SSE event volume / parse cost, to correlate whole-
// machine stutter during heavy OCR with the log-streaming load.
let probeSince = performance.now();
let probeEvents = 0;
let probeBytes = 0;
let probeMaxMs = 0;
function probeSse(kind: string, bytes: number, started: number) {
  probeEvents += 1;
  probeBytes += bytes;
  const ms = performance.now() - started;
  if (ms > probeMaxMs) probeMaxMs = ms;
  const now = performance.now();
  if (now - probeSince >= 30000) {
    const secs = (now - probeSince) / 1000;
    console.warn(
      `[PROBE][SSE] ${kind}: ${probeEvents} events, ${(probeBytes / 1024).toFixed(1)}KB, maxParseMs=${probeMaxMs.toFixed(1)}, ${(probeEvents / secs).toFixed(1)}/s`,
    );
    probeEvents = 0;
    probeBytes = 0;
    probeMaxMs = 0;
    probeSince = now;
  }
}

export function connectEvents() {
  if (es) {
    return;
  }
  const url = `${BASE}/sse`;
  es = new EventSource(url);
  es.onopen = () => {
    connState.connected = true;
  };
  es.addEventListener("status", (event) => {
    const started = performance.now();
    const data = (event as MessageEvent<string>).data;
    Object.assign(status, JSON.parse(data) as Status);
    probeSse("status", data.length, started);
  });
  es.addEventListener("log", (event) => {
    const started = performance.now();
    const data = (event as MessageEvent<string>).data;
    const { instance, logs: newLogs, reset } = JSON.parse(data) as SseLog;
    if (reset) {
      // Backend re-sent the whole buffer (initial connect / backend trim).
      // Replace the array identity so LogView rebuilds.
      logs[instance] = [...newLogs];
    } else {
      const buf = (logs[instance] ??= []);
      buf.push(...newLogs);
      if (buf.length > 800) {
        // Trim in chunks with identity replacement so LogView rebuilds
        // rarely (every ~300 lines) instead of re-rendering every second.
        logs[instance] = buf.slice(-500);
      }
    }
    probeSse("log", data.length, started);
  });
  es.addEventListener("scheduler", (event) => {
    const started = performance.now();
    const data = (event as MessageEvent<string>).data;
    const { instance, ...snapshot } = JSON.parse(data) as SchedulerSnapshot & {
      instance: string;
    };
    schedulers[instance] = snapshot;
    probeSse("scheduler", data.length, started);
  });
  es.onerror = () => {
    connState.connected = false;
    es?.close();
    es = null;
    reconnectTimer = window.setTimeout(connectEvents, 2000);
  };
}

export function disconnectEvents() {
  window.clearTimeout(reconnectTimer);
  es?.close();
  es = null;
}
