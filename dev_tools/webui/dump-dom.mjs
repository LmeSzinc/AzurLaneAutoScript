/** One-off: dump the rendered DOM of a URL to inspect what the app mounted. */
import { spawn } from "node:child_process";
import { mkdirSync } from "node:fs";
import { join } from "node:path";

const PORT = Number(process.argv[2] ?? 8117);
const PAGE_URL = process.argv[3] ?? `http://127.0.0.1:${PORT}/#/settings?task=Alas`;
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
    await send("Page.navigate", { url: PAGE_URL });
    await sleep(5000);
    const r = await send("Runtime.evaluate", {
      expression: "document.body.innerHTML",
      returnByValue: true,
    });
    console.log(r.result.value.slice(0, 6000));
    ws.close();
  } finally {
    edge.kill();
  }
}

await main();
