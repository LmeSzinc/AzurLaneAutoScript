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

$effect(() => {
  const node = codeEl;
  const pre = preEl;
  if (!node || !pre) return;
  if (lines !== lastArray) {
    // Buffer replaced: instance switch, chunked trim or backend reset.
    lastArray = lines;
    rebuild();
  } else if (lines.length < renderedCount) {
    // Buffer spliced in place.
    rebuild();
  } else if (lines.length > renderedCount) {
    node.insertAdjacentHTML("beforeend", ansiToHtml(`${lines.slice(renderedCount).join("\n")}\n`));
    renderedCount = lines.length;
  }
  if (keepBottom) {
    pre.scrollTop = pre.scrollHeight;
  }
});
</script>

<pre class={cls} bind:this={preEl}><code bind:this={codeEl}></code></pre>
