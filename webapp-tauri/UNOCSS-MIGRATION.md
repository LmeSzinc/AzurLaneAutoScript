# UnoCSS migration

The SPA shell was migrated from the vendored Bootswatch v4.6.1 themes +
legacy pywebio-era CSS (≈900KB across 15 files) to a single UnoCSS layer
(≈31KB CSS) that replicates the original UI pixel for pixel.

## Architecture

```
src/styles/theme.css   design tokens (single source of truth)
                       :root = light shell + default palette
                       [data-theme="dark|minty|yeti|sketchy"] = overrides
src/styles/base.css    element-level rules (reboot gaps, scrollbars, p/h4,
                       box-sizing, spinner keyframes)
uno.config.ts          presetUno + shortcuts (btn*, form-control*, table,
                       alert, panels, logs, header states) + safelist
```

- **Theming** is one attribute: `<html data-theme="...">`. The old runtime
  `<link>` swapping (Bootswatch + light/dark shell overrides) is gone, along
  with its FOUC and cascade-order fragility. `App.svelte` + `main.ts` set
  `data-theme` before mount.
- **Tokens** were extracted from the vendored theme files
  (`dev_tools/webui/extract_themes.py` → `theme-extract.json`), then
  corrected against pixel captures of the real old UI (the extractor can
  over-merge selector blocks; the captures are ground truth).
- **Semantic classes** (`btn`, `form-control`, `table`, `alert`, ...) are
  UnoCSS shortcuts built from utilities, so the Svelte markup keeps its
  meaning while every color/measurement references a `--alas-*` token.
- **Conditional classes** (`class:btn-on={...}`, classes chosen in script
  expressions) are not extracted by UnoCSS from Svelte files — they live in
  the config `safelist`.
- Legacy `public/css/*` (Bootswatch, bootstrap-select, pywebio-era
  alas*.css) was deleted; only `public/icon/` remains.

## Faithful-replication pitfalls fixed during the migration

- Bootstrap reboot used `box-sizing: border-box` globally; the UnoCSS
  preflight does not → fixed heights would have overflowed by padding.
- The bootswatch `.form-control` (loaded after the shell css) wins the
  cascade: real padding is `.375rem .75rem`, not the shell override.
- Table cells are transparent everywhere except the sketchy theme.
- Tailwind `text-xl`/`text-sm` utilities pair font-size with Tailwind
  line-heights; the old UI inherited `line-height: 1.5` — titles use bare
  `text-[1.25rem]` etc.
- The UnoCSS preflight keeps UA `p { margin: 1em 0 }`; bootstrap reboot used
  `margin-top: 0; margin-bottom: 1rem` → restored in `base.css`.
- Checkbox `accent-color` is a constant `#7a77bb` (the old light shell
  hardcoded it, ignoring the accent token).
- Per-theme form-control `font-weight` (sketchy uses 700) is a token.

## Verification

`dev_tools/webui/` contains a CDP-based capture harness and pixel-diff
tooling. Baselines of the original UI (`baseline-old/`, built from the
parent commit) are compared against the migrated UI for 4 routes × 5 themes
at 1280×800; the current result is 0.5–3.3% differing pixels per pair
(threshold 2%), with the remainder being 1px border/antialiasing noise on
the sketchy/yeti themes. See `dev_tools/webui/README.md`.
