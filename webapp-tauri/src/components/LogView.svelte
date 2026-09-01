<script lang="ts">
import { ansiToHtml } from "../lib/ansi";

interface Props {
  lines: string[];
  class?: string;
  keepBottom?: boolean;
}

let { lines, class: cls = "", keepBottom = true }: Props = $props();
let preEl = $state<HTMLElement | null>(null);
let codeEl = $state<HTMLElement | null>(null);

// Incremental log view: append only newly arrived lines instead of
// rebuilding the whole buffer (which caused per-second full DOM re-layout
// and system-wide stutter). Full rebuilds only happen when the store
// replaces the buffer (instance switch / trim / backend reset).
let lastArray: string[] | null = null;
let renderedCount = 0;
let scrollRaf: number | undefined;

function scheduleScroll() {
  // Coalesce keep-bottom scrolling into one layout pass per animation
  // frame; assigning scrollTop synchronously inside the effect forced a
  // full reflow of the log container on every SSE batch (system-wide
  // stutter during high-rate log streaming).
  if (scrollRaf !== undefined) return;
  scrollRaf = requestAnimationFrame(() => {
    scrollRaf = undefined;
    const pre = preEl;
    if (pre && keepBottom) {
      pre.scrollTop = pre.scrollHeight;
    }
  });
}

function rebuild() {
  const node = codeEl;
  if (!node) return;
  node.textContent = "";
  renderedCount = 0;
  if (lines.length > 0) {
    node.insertAdjacentHTML("beforeend", ansiToHtml(`${lines.join("\n")}\n`));
    renderedCount = lines.length;
  }
}

// PROBE: temporary instrumentation (revert with the probe commit).
// 30-second summary of DOM-render cost per SSE batch, to correlate whole-
// machine stutter during heavy OCR with log-view layout/insert work.
let probeSince = performance.now();
let probeAppends = 0;
let probeLines = 0;
let probeTotalMs = 0;
let probeMaxMs = 0;
function probeRender(ms: number, linesDelta: number) {
  probeAppends += 1;
  probeLines += linesDelta;
  probeTotalMs += ms;
  if (ms > probeMaxMs) probeMaxMs = ms;
  const now = performance.now();
  if (now - probeSince >= 30000) {
    console.warn(
      `[PROBE][LogView] ${probeAppends} appends, ${probeLines} lines, avg=${(probeTotalMs / probeAppends).toFixed(2)}ms, max=${probeMaxMs.toFixed(1)}ms`,
    );
    probeAppends = 0;
    probeLines = 0;
    probeTotalMs = 0;
    probeMaxMs = 0;
    probeSince = now;
  }
}

$effect(() => {
  const node = codeEl;
  const pre = preEl;
  if (!node || !pre) return;
  if (lines !== lastArray) {
    // Buffer replaced: instance switch, chunked trim or backend reset.
    lastArray = lines;
    const t0 = performance.now();
    rebuild();
    probeRender(performance.now() - t0, lines.length);
  } else if (lines.length < renderedCount) {
    // Buffer spliced in place.
    const t0 = performance.now();
    rebuild();
    probeRender(performance.now() - t0, lines.length);
  } else if (lines.length > renderedCount) {
    const t0 = performance.now();
    node.insertAdjacentHTML("beforeend", ansiToHtml(`${lines.slice(renderedCount).join("\n")}\n`));
    const delta = lines.length - renderedCount;
    renderedCount = lines.length;
    probeRender(performance.now() - t0, delta);
  }
  scheduleScroll();
});

// Re-arm follow scrolling when the user toggles scroll lock back on.
$effect(() => {
  if (keepBottom) scheduleScroll();
});
</script>

<pre class={cls} bind:this={preEl}><code bind:this={codeEl}></code></pre>
