# webui visual regression harness

Deterministic screenshot tooling used to verify the UnoCSS migration
replicates the original UI pixel for pixel. Everything is dependency-free
(Node built-ins + Edge headless + PIL).

## Layout

- `mock.mjs` — mock backend for the SPA. Serves `webapp-tauri/dist` and
  answers the REST/SSE endpoints with realistic content (menu, schema,
  scheduler rows, configs, real zh-CN i18n) so every page renders
  meaningfully. Theme is switched at runtime by writing `mock-theme.txt`.
- `capture.mjs` — CDP-driven screenshot capture (1280×800). Plain
  `msedge --screenshot` fires on the load event and races the SPA's
  post-mount fetches; this harness waits for the route content to render
  before capturing.
- `probe.mjs` / `dump-dom.mjs` — one-off CDP probes (computed styles, DOM).
- `diff.py` — pairwise pixel diff of two screenshot trees; writes heatmaps.
- `profile.py` — per-band diff localization.
- `colorpairs.py` — dominant old→new color transitions in a diff.
- `extract_themes.py` — parses the vendored Bootswatch v4.6.1 files into
  `theme-extract.json`; the design tokens in `src/styles/theme.css` were
  authored from that extraction.
- `flatten_i18n.py` — flattens `module/config/i18n/<lang>.json` (depth 3,
  like `module.webui.lang.reload`) into `mock-i18n-<lang>.json` for the mock.

## Usage

```powershell
# 1. flatten the dictionary the mock serves
.\.venv\Scripts\python.exe dev_tools/webui/flatten_i18n.py zh-CN

# 2. run the mock (keep it alive for the capture run)
$env:MOCK_LANG='zh-CN'; node dev_tools/webui/mock.mjs 8117

# 3. build the frontend you want to capture (old or new UI), then capture
node dev_tools/webui/capture.mjs dev_tools/webui/baseline-new

# 4. compare against the baseline
.\.venv\Scripts\python.exe dev_tools/webui/diff.py dev_tools/webui/baseline-old dev_tools/webui/baseline-new
```

## Baseline status

`baseline-old/` holds captures of the pre-migration UI (Bootswatch 4.6.1 +
legacy shell CSS, built from the parent commit). A pair is "OK" when ≤ 2%
of pixels differ; the current migration measures 0.5–3.3% per pair, with
the remaining pixels being 1px border/antialiasing noise on the
sketchy/yeti themes.
