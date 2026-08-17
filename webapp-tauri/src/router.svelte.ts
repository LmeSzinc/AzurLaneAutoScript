/** Minimal hash router: #/, #/develop, #/manage, #/settings?task=X */
export const KNOWN_PATHS = ["/", "/develop", "/manage", "/settings"];

export const route = $state<{ path: string; query: Record<string, string> }>({
  path: "/",
  query: {},
});

function parseHash() {
  const raw = window.location.hash.replace(/^#/, "") || "/";
  const [pathPart, queryPart] = raw.split("?");
  const query: Record<string, string> = {};
  if (queryPart) {
    for (const pair of queryPart.split("&")) {
      const [key, value] = pair.split("=");
      if (key) {
        query[decodeURIComponent(key)] = decodeURIComponent(value ?? "");
      }
    }
  }
  route.path = pathPart || "/";
  route.query = query;
  if (!KNOWN_PATHS.includes(route.path)) {
    // Unmatched route: land on home and rewrite the URL hash (replace
    // keeps the stray route out of browser history). Mirrors the
    // server-side 302-to-home policy for unmatched paths.
    route.path = "/";
    route.query = {};
    if (window.location.hash) {
      window.location.replace("#/");
    }
  }
}

export function initRouter() {
  window.addEventListener("hashchange", parseHash);
  parseHash();
}

export function push(path: string, query?: Record<string, string>) {
  const qs = query ? "?" + new URLSearchParams(query).toString() : "";
  window.location.hash = path + qs;
}

export function replace(path: string, query?: Record<string, string>) {
  const qs = query ? "?" + new URLSearchParams(query).toString() : "";
  const url = "#" + path + qs;
  if (window.location.hash === url) {
    // Same hash: force a manual parse so state updates.
    parseHash();
    return;
  }
  window.location.replace(url);
}
