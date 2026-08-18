/**
 * Minimal mock backend for visual regression captures of the SPA shell.
 *
 * Serves webapp-tauri/dist statically and answers the REST/SSE endpoints the
 * frontend calls, with realistic sample content (menu, schema, scheduler
 * rows, configs) so every page renders meaningfully without the Python
 * backend.
 *
 * Usage:
 *   node dev_tools/webui/mock.mjs [port]            # default 8117
 *   MOCK_THEME=dark MOCK_LANG=zh-CN node ...        # theme/language to serve
 */

import { createServer } from "node:http";
import { createReadStream, existsSync, readFileSync, statSync } from "node:fs";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(fileURLToPath(import.meta.url), "..", "..", "..");
const DIST = join(ROOT, "webapp-tauri", "dist");
const PORT = Number(process.argv[2] ?? 8117);
const THEME_FILE = join(ROOT, "dev_tools", "webui", "mock-theme.txt");
const LANG = process.env.MOCK_LANG ?? "zh-CN";

/** Theme is re-read on every /status request so capture scripts can switch
 *  themes on a long-lived server without port/process races. */
function currentTheme() {
  try {
    const t = readFileSync(THEME_FILE, "utf-8").trim();
    if (t) return t;
  } catch {
    // file absent: fall through to env
  }
  return process.env.MOCK_THEME ?? "dark";
}

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".ico": "image/x-icon",
  ".map": "application/json",
};

function i18nDict() {
  const file = join(ROOT, "dev_tools", "webui", `mock-i18n-${LANG}.json`);
  if (!existsSync(file)) return {};
  return JSON.parse(readFileSync(file, "utf-8"));
}

function statusBody() {
  return {
    instances: [{ name: "alas", state: 0, alive: false, pid: 0, message: "" }],
    theme: currentTheme(),
    language: LANG,
  };
}

const MENU = {
  Alas: { menu: "unfold", page: "form", tasks: ["Alas"] },
  Reward: { menu: "unfold", page: "form", tasks: ["Reward"] },
  Raid: { menu: "unfold", page: "form", tasks: ["Raid"] },
  Tool: { menu: "collapse", page: "tool", tasks: ["Emulator", "GameManager"] },
};

const ARGS = {
  Alas: {
    Emulator: {
      Serial: { display: "show", type: "select", option: ["auto", "127.0.0.1:5555"], value: "auto" },
      EmulatorPath: { display: "show", type: "text", value: "C:\\Program Files\\BlueStacks\\HD-Player.exe" },
      PerformanceMode: { display: "show", type: "checkbox", value: true },
      Resolution: { display: "show", type: "select", option: ["1280x720", "1600x900", "1920x1080"], value: "1280x720" },
      NextRun: { display: "show", type: "datetime", value: "2026-01-01 00:00:00" },
      LockState: { display: "show", type: "lock", value: "Idle", option_bold: ["Idle"] },
    },
    Storage: {
      Storage: { display: "show", type: "storage", value: {} },
    },
  },
};

const SCHEDULER = {
  alive: false,
  running: [{ command: "Alas", next_run: "2026-01-01 08:00:00" }],
  pending: [
    { command: "Alas", next_run: "2026-01-01 08:00:00" },
    { command: "Reward", next_run: "2026-01-01 09:00:00" },
  ],
  waiting: [
    { command: "Raid", next_run: "2026-01-01 10:00:00" },
    { command: "Reward", next_run: "2026-01-02 09:00:00" },
    { command: "Raid", next_run: "2026-01-02 10:00:00" },
    { command: "Reward", next_run: "2026-01-03 09:00:00" },
    { command: "Raid", next_run: "2026-01-03 10:00:00" },
    { command: "Reward", next_run: "2026-01-04 09:00:00" },
    { command: "Raid", next_run: "2026-01-04 10:00:00" },
  ],
};

function json(res, code, body) {
  res.writeHead(code, { "Content-Type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(body));
}

function apiRoute(req, res, url) {
  const { pathname } = url;
  if (pathname === "/status") return json(res, 200, statusBody());
  if (pathname === "/sse") {
    res.writeHead(200, {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    });
    res.write(": connected\n\n");
    const timer = setInterval(() => res.write(": keep-alive\n\n"), 15000);
    res.on("close", () => clearInterval(timer));
    return;
  }
  const i18n = pathname.match(/^\/i18n\/([\w-]+)$/);
  if (i18n) return json(res, 200, i18nDict());
  const schema = pathname.match(/^\/schema\/(\w+)$/);
  if (schema) return json(res, 200, { menu: MENU, args: ARGS });
  const config = pathname.match(/^\/config\/([\w-]+)$/);
  if (config) return json(res, 200, {});
  const scheduler = pathname.match(/^\/scheduler\/([\w-]+)$/);
  if (scheduler) return json(res, 200, SCHEDULER);
  if (pathname === "/configs") {
    return json(res, 200, [
      { name: "alas", modified: "2026-01-01 12:00:00" },
      { name: "second", modified: "2025-12-01 12:00:00" },
    ]);
  }
  if (pathname === "/update/status") return json(res, 200, { state: "idle", current: null });
  if (pathname === "/update/history") {
    return json(res, 200, {
      local: ["4a2db0fe", "Author", "2026-01-01", "fix(webui): define ANSI palette CSS vars"],
      upstream: ["4a2db0fe", "Author", "2026-01-01", "fix(webui): define ANSI palette CSS vars"],
      history: [
        ["4a2db0fe", "LmeSzinc", "2026-01-01", "fix(webui): define ANSI palette CSS vars so log colors resolve"],
        ["e147df34", "LmeSzinc", "2025-12-30", "fix(shell): add updater pubkey config; fix Home overview scrollbars"],
      ],
    });
  }
  if (pathname === "/update/check" || pathname === "/update/run" || pathname === "/language" || pathname === "/theme") {
    return json(res, 200, { ok: true });
  }
  return null;
}

function serveStatic(req, res, pathname) {
  const safe = normalize(pathname).replace(/^(\.\.(\/|\\|$))+/, "");
  let file = join(DIST, safe === "/" ? "index.html" : safe);
  if (!existsSync(file) || statSync(file).isDirectory()) file = join(DIST, "index.html");
  res.writeHead(200, { "Content-Type": MIME[extname(file)] ?? "application/octet-stream" });
  createReadStream(file).pipe(res);
}

createServer((req, res) => {
  const url = new URL(req.url ?? "/", `http://127.0.0.1:${PORT}`);
  if (apiRoute(req, res, url) !== null) return;
  serveStatic(req, res, url.pathname);
}).listen(PORT, "127.0.0.1", () => {
  console.log(`mock webui backend on http://127.0.0.1:${PORT} (lang=${LANG})`);
});
