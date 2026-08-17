/**
 * Convert ANSI SGR-colored text (as produced by rich with color_system='standard')
 * to theme-aware HTML using Bootstrap CSS variables. The text is HTML-escaped
 * first, so the result is safe to render via {@html}.
 */
const SGR_FG: Record<string, string> = {
  "30": "var(--bs-body-color)",
  "31": "var(--bs-danger)",
  "32": "var(--bs-success)",
  "33": "var(--bs-warning)",
  "34": "var(--bs-primary)",
  "35": "#d63384",
  "36": "var(--bs-info)",
  "37": "var(--bs-body-color)",
  "90": "var(--bs-secondary)",
  "91": "#ff8090",
  "92": "#8be9a8",
  "93": "#ffe08a",
  "94": "#9ec5fe",
  "95": "#e599f7",
  "96": "#9eeaf9",
  "97": "var(--bs-body-color)",
};

const SGR_BG: Record<string, string> = {
  "40": "var(--bs-dark)",
  "41": "var(--bs-danger)",
  "42": "var(--bs-success)",
  "43": "var(--bs-warning)",
  "44": "var(--bs-primary)",
  "45": "#d63384",
  "46": "var(--bs-info)",
  "47": "var(--bs-secondary)",
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
