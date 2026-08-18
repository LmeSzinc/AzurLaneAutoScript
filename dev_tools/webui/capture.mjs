/**
 * Deterministic screenshot capture via CDP (Edge headless).
 *
 * The plain `msedge --screenshot` flag captures on the load event, racing
 * the SPA's post-mount fetches, which produced blank/flaky baselines. This
 * harness drives the page over the DevTools protocol and waits for the app
 * to actually render before capturing.
 *
 * Usage: node dev_tools/webui/capture.mjs [outDir] [port]
 * Themes are switched via the long-lived mock server (mock-theme.txt).
 */

import { mkdirSync, writeFileSync } from "node:fs";
import { spawn } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const THEME_FILE = join(HERE, "mock-theme.txt");
const OUT = process.argv[2] ? join(process.cwd(), process.argv[2]) : join(HERE, "baseline");
const PORT = Number(process.argv[3] ?? 8117);
const EDGE = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const THEMES = ["default", "dark", "minty", "yeti", "sketchy"];
const ROUTES = [
  // selectors exist in both the old and the new UI implementations
  ["home", `http://127.0.0.1:${PORT}/#/`, ".overview-task"], // scheduler rows loaded
  ["develop", `http://127.0.0.1:${PORT}/#/develop`, "#app main > div"],
  ["manage", `http://127.0.0.1:${PORT}/#/manage`, "tbody tr"], // config rows loaded
  // settings renders its group cards after the schema fetch resolves
  ["settings", `http://127.0.0.1:${PORT}/#/settings?task=Alas`, ".group-card"],
];
// App ready: mounted, theme mechanism applied (old app: dynamic bootswatch
// link; new app: data-theme attribute), and the route content rendered.
const READY = `document.querySelector("#app").childElementCount > 0 && ` +
  `(document.documentElement.dataset.theme || document.querySelector('link[href*=".min.css"]'))`;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

class CDP {
  constructor(ws) {
    this.ws = ws;
    this.id = 0;
    this.pending = new Map();
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.id && this.pending.has(msg.id)) {
        const { resolve, reject } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        if (msg.error) reject(new Error(JSON.stringify(msg.error)));
        else resolve(msg.result);
      }
    };
  }
  send(method, params = {}) {
    const id = ++this.id;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }
  static async connect(port) {
    for (let i = 0; i < 50; i++) {
      try {
        const res = await fetch(`http://127.0.0.1:${port}/json/list`);
        const targets = await res.json();
        const page = targets.find((t) => t.type === "page");
        if (page) {
          const ws = new WebSocket(page.webSocketDebuggerUrl, { headers: {} });
          await new Promise((resolve, reject) => {
            ws.onopen = resolve;
            ws.onerror = reject;
          });
          return new CDP(ws);
        }
      } catch {
        // not up yet
      }
      await sleep(200);
    }
    throw new Error(`no CDP target on port ${port}`);
  }
}

async function capturePage(debugPort, url, waitSelector, outFile) {
  const cdp = await CDP.connect(debugPort);
  await cdp.send("Page.enable");
  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width: 1280,
    height: 800,
    deviceScaleFactor: 1,
    mobile: false,
  });
  await cdp.send("Page.navigate", { url });
  // Wait for the app to mount, the theme to apply, and the route content.
  const condition = `${READY} && document.querySelector(${JSON.stringify(waitSelector)})`;
  let ready = false;
  for (let i = 0; i < 100 && !ready; i++) {
    await sleep(200);
    try {
      const r = await cdp.send("Runtime.evaluate", { expression: condition, returnByValue: true });
      ready = Boolean(r.result.value);
    } catch {
      // page still navigating
    }
  }
  if (!ready) throw new Error(`app never became ready for ${url}`);
  await sleep(1500); // let fonts/layout settle
  const shot = await cdp.send("Page.captureScreenshot", { format: "png" });
  writeFileSync(outFile, Buffer.from(shot.data, "base64"));
  cdp.ws.close();
}

async function run() {
  for (const theme of THEMES) {
    // Tell the mock server which theme /status should report.
    writeFileSync(THEME_FILE, theme);
    const themeDir = join(OUT, theme);
    mkdirSync(themeDir, { recursive: true });
    for (const [name, url, waitSelector] of ROUTES) {
      const debugPort = 9300 + Math.floor(Math.random() * 300);
      const profile = join(process.env.TEMP, `edge-cdp-${Date.now()}-${Math.random().toString(16).slice(2)}`);
      mkdirSync(profile, { recursive: true });
      const edge = spawn(
        EDGE,
        [
          "--headless=new",
          "--disable-gpu",
          "--no-first-run",
          "--no-default-browser-check",
          "--remote-allow-origins=*",
          "--window-size=1280,800",
          `--remote-debugging-port=${debugPort}`,
          `--user-data-dir=${profile}`,
          "about:blank",
        ],
        { stdio: "ignore" },
      );
      try {
        await capturePage(debugPort, url, waitSelector, join(themeDir, `${name}.png`));
        console.log(`captured ${theme}/${name}`);
      } finally {
        edge.kill();
        await sleep(300);
      }
    }
  }
  console.log(`done -> ${OUT}`);
}

await run();
