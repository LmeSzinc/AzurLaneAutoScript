import { defineConfig, presetUno, transformerVariantGroup } from "unocss";

/**
 * Alas styling on UnoCSS (v2 — utility-first).
 *
 * Components are composed from utilities in the markup; only genuinely
 * repeated composites live here:
 *  - `btn` / `btn-sm`: button anatomy only (layout, metrics, focus,
 *    disabled) — NO colors, so variants compose freely in markup
 *    (`class="btn bg-primary text-white hover:bg-primary-hover"`).
 *  - `panel`: bordered surface used by sections/cards/bars.
 *  - `table`: bootstrap-style table with token-driven borders.
 *
 * Theme colors map to the --*-v2 tokens in src/styles/theme.css; state
 * shades (hover/active) are derived from the palette with color-mix().
 * The active theme is the `data-theme` attribute on <html>.
 */
export default defineConfig({
  presets: [presetUno()],
  transformers: [transformerVariantGroup()],
  // UnoCSS does not extract names used only inside Svelte `class:xxx`
  // directives or computed class strings; keep every dynamic class here.
  safelist: [
    "bg-status-idle",
    "bg-status-running",
    "bg-status-warning",
    "bg-status-updating",
    "bg-accent",
    "bg-surface-app",
    "text-white",
    "text-body",
    "border-toggle",
    "border-l-accent",
    "pl-[3px]",
    "font-bold",
    "text-accent",
    "text-muted",
    "rotate-90",
    "my-[0.125rem]",
    "my-[0.375rem]",
  ],
  theme: {
    colors: {
      surface: {
        app: "var(--surface-app)",
        panel: "var(--surface-panel)",
        side: "var(--surface-side)",
        insert: "var(--surface-insert)",
        hover: "var(--surface-hover)",
        hr: "var(--surface-hr)",
        log: "var(--surface-log)",
      },
      line: {
        panel: "var(--line-panel)",
        control: "var(--line-control)",
        task: "var(--line-task)",
        toggle: "var(--toggle-line)",
        soft: "var(--line-soft)",
      },
      body: "var(--text-body)",
      muted: "var(--text-muted)",
      input: "var(--input-fg)",
      accent: "var(--accent)",
      icon: "var(--icon-fill)",
      status: {
        idle: "var(--status-idle)",
        running: "var(--status-running)",
        warning: "var(--status-warning)",
        updating: "var(--status-updating)",
      },
      primary: "var(--color-primary)",
      "primary-hover": "color-mix(in srgb, var(--color-primary) 88%, #000)",
      "primary-active": "color-mix(in srgb, var(--color-primary) 78%, #000)",
      success: "var(--color-success)",
      "success-hover": "color-mix(in srgb, var(--color-success) 88%, #000)",
      "success-active": "color-mix(in srgb, var(--color-success) 78%, #000)",
      info: "var(--color-info)",
      "info-hover": "color-mix(in srgb, var(--color-info) 88%, #000)",
      "info-active": "color-mix(in srgb, var(--color-info) 78%, #000)",
      danger: "var(--color-danger)",
      gray: {
        300: "var(--gray-300)",
        400: "var(--gray-400)",
        500: "var(--gray-500)",
        600: "var(--gray-600)",
        800: "var(--gray-800)",
      },
    },
  },
  shortcuts: {
    // Button anatomy (no colors). Metrics are theme tokens because the
    // themes have distinct typography (yeti 300, sketchy 2px border, ...).
    btn:
      "inline-flex items-center justify-center select-none border-solid [border-width:var(--btn-bw)] " +
      "[padding:var(--btn-py)_var(--btn-px)] [font-size:var(--text-btn)] [font-weight:var(--btn-fw)] " +
      "[line-height:1.5] [font-family:var(--btn-font,inherit)] rounded-[var(--radius-btn)] " +
      "transition-colors focus:outline-none focus:shadow-none disabled:opacity-65",
    "btn-sm":
      "inline-flex items-center justify-center select-none border-solid [border-width:var(--btn-bw)] " +
      "[padding:var(--btn-sm-py)_var(--btn-sm-px)] [font-size:var(--text-btn-sm)] [font-weight:var(--btn-fw)] " +
      "[line-height:1.5] [font-family:var(--btn-font,inherit)] rounded-[var(--radius-btn-sm)] " +
      "transition-colors focus:outline-none focus:shadow-none disabled:opacity-65",
    // Bordered surface (sections, cards, bars).
    panel: "border border-solid border-line-panel bg-surface-panel",
    // Every table in the app uses the compact cell padding (.3rem).
    table:
      "w-full [margin-bottom:1rem] [color:var(--text-body)] [border-collapse:collapse] " +
      "[&_th,&_td]:p-1.2 [&_th,&_td]:align-top [&_th,&_td]:[border-top:var(--line-table)] " +
      "[&_th,&_td]:[background:var(--table-cell-bg)] " +
      "[&_thead_th]:align-bottom [&_thead_th]:[border-bottom:var(--line-table-strong)]",
  },
});
