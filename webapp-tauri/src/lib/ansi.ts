/**
 * Convert ANSI SGR-colored text (as produced by rich with color_system='standard')
 * to theme-aware HTML. The text is HTML-escaped first, so the result is safe to
 * render via {@html}.
 *
 * Color codes 30-37/40-47/90-97 map to the --ansi-* CSS custom properties
 * defined in css/alas-shell.css (dark palette, the pywebio-era
 * DARK_TERMINAL_THEME) and overridden by css/light-alas-shell.css
 * (LIGHT_TERMINAL_THEME) for light themes. Each reference carries the dark
 * value as a fallback so the mapping degrades gracefully if the theme CSS
 * has not loaded yet.
 *
 * The previous mapping used var(--bs-primary) etc., but the bundled
 * Bootstrap themes are pre-CSS-variable versions that never define those
 * properties, so level/time colors silently resolved to nothing.
 */
const SGR_FG: Record<string, string> = {
  "30": "var(--ansi-black, #000000)",
  "31": "var(--ansi-red, #cd3131)",
  "32": "var(--ansi-green, #0dbc79)",
  "33": "var(--ansi-yellow, #e5e510)",
  "34": "var(--ansi-blue, #2472c8)",
  "35": "var(--ansi-magenta, #bc3fbc)",
  "36": "var(--ansi-cyan, #11a8cd)",
  "37": "var(--ansi-white, #e5e5e5)",
  "90": "var(--ansi-bright-black, #666666)",
  "91": "var(--ansi-bright-red, #f14c4c)",
  "92": "var(--ansi-bright-green, #23d18b)",
  "93": "var(--ansi-bright-yellow, #f5f543)",
  "94": "var(--ansi-bright-blue, #3b8eea)",
  "95": "var(--ansi-bright-magenta, #d670d6)",
  "96": "var(--ansi-bright-cyan, #29b8db)",
  "97": "var(--ansi-bright-white, #e5e5e5)",
};

const SGR_BG: Record<string, string> = {
  "40": "var(--ansi-black, #000000)",
  "41": "var(--ansi-red, #cd3131)",
  "42": "var(--ansi-green, #0dbc79)",
  "43": "var(--ansi-yellow, #e5e510)",
  "44": "var(--ansi-blue, #2472c8)",
  "45": "var(--ansi-magenta, #bc3fbc)",
  "46": "var(--ansi-cyan, #11a8cd)",
  "47": "var(--ansi-white, #e5e5e5)",
};

function escapeHtml(text: string): string {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

export function ansiToHtml(text: string): string {
  const escaped = escapeHtml(text);
  let out = "";
  let pendingClose = false;
  const re = /\x1b\[([0-9;]*)m/g;
  let last = 0;
  let match: RegExpExecArray | null;
  while ((match = re.exec(escaped))) {
    out += escaped.slice(last, match.index);
    if (pendingClose) {
      out += "</span>";
      pendingClose = false;
    }
    const codes = match[1] ? match[1].split(";") : ["0"];
    const styles: string[] = [];
    for (const code of codes) {
      if (code === "0" || code === "") continue;
      if (code === "1") styles.push("font-weight:700");
      else if (code === "3") styles.push("font-style:italic");
      else if (code === "4") styles.push("text-decoration:underline");
      else if (SGR_FG[code]) styles.push(`color:${SGR_FG[code]}`);
      else if (SGR_BG[code]) styles.push(`background:${SGR_BG[code]}`);
    }
    if (styles.length) {
      out += `<span style="${styles.join(";")}">`;
      pendingClose = true;
    }
    last = re.lastIndex;
  }
  out += escaped.slice(last);
  if (pendingClose) out += "</span>";
  return out;
}
