/** One-off CDP probe: evaluate a JS expression in a page and print the result. */
import { spawn } from "node:child_process";
import { mkdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

const PORT = Number(process.argv[2] ?? 8117);
const PAGE_URL = process.argv[3] ?? `http://127.0.0.1:${PORT}/#/`;
// expression: inline string, or a path to a .js file (read from disk)
const EXPR = process.argv[4]?.endsWith(".js")
  ? readFileSync(process.argv[4], "utf-8")
  : process.argv[4] ?? "document.body.innerHTML.slice(0, 4000)";
const EDGE = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function main() {
  const debugPort = 9400 + Math.floor(Math.random() * 100);
  const profile = join(process.env.TEMP, `edge-dump-${Date.now()}`);
  mkdirSync(profile, { recursive: true });
  const edge = spawn(
    EDGE,
    ["--headless=new", "--disable-gpu", "--no-first-run", "--remote-allow-origins=*", `--remote-debugging-port=${debugPort}`, `--user-data-dir=${profile}`, "about:blank"],
    { stdio: "ignore" },
  );
  try {
    let target = null;
    for (let i = 0; i < 50 && !target; i++) {
      await sleep(200);
      try {
        const res = await fetch(`http://127.0.0.1:${debugPort}/json/list`);
        target = (await res.json()).find((t) => t.type === "page");
      } catch {}
    }
    const ws = new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((r, j) => ((ws.onopen = r), (ws.onerror = j)));
    let id = 0;
    const pending = new Map();
    ws.onmessage = (ev) => {
      const m = JSON.parse(ev.data);
      if (m.id && pending.has(m.id)) {
        pending.get(m.id)(m.result);
        pending.delete(m.id);
      }
    };
    const send = (method, params = {}) =>
      new Promise((r) => {
        const mid = ++id;
        pending.set(mid, r);
        ws.send(JSON.stringify({ id: mid, method, params }));
      });
    await send("Page.enable");
    await send("Emulation.setDeviceMetricsOverride", {
      width: 1280,
      height: 800,
      deviceScaleFactor: 1,
      mobile: false,
    });
    await send("Page.navigate", { url: PAGE_URL });
    // Poll until the app is mounted and the route content exists.
    const readyExpr =
      `document.querySelector("#app")?.childElementCount > 0 && ` +
      `(document.documentElement.dataset.theme || document.querySelector('link[href*=".min.css"]')) && ` +
      `document.querySelector(".form-field, .group-card, .overview-task, tbody tr, .center-text")`;
    for (let i = 0; i < 60; i++) {
      await sleep(300);
      try {
        const rr = await send("Runtime.evaluate", { expression: readyExpr, returnByValue: true });
        if (rr.result?.value) break;
      } catch {}
    }
    await sleep(1200);
    const r = await send("Runtime.evaluate", { expression: EXPR, returnByValue: true });
    if (r.exceptionDetails) console.log("EXCEPTION:", JSON.stringify(r.exceptionDetails, null, 2));
    else console.log(typeof r.result?.value === "string" ? r.result.value : JSON.stringify(r.result?.value, null, 2));
    ws.close();
  } finally {
    edge.kill();
  }
}

await main();
