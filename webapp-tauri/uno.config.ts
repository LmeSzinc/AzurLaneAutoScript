import { defineConfig, presetUno, transformerDirectives, transformerVariantGroup } from "unocss";

/**
 * Alas shell styling on UnoCSS.
 *
 * Semantic component classes (btn, form-control, table, ...) are shortcuts
 * built from utilities; every color/measurement references the --alas-*
 * design tokens in src/styles/theme.css, so all five themes share one
 * stylesheet and theme switching is a single `data-theme` attribute flip.
 */
export default defineConfig({
  presets: [presetUno()],
  transformers: [transformerDirectives(), transformerVariantGroup()],
  // UnoCSS does not extract names used only inside Svelte `class:xxx`
  // directives; keep them in the safelist so conditional classes always
  // generate.
  safelist: [
    "btn-on",
    "btn-off",
    "btn-primary",
    "btn-adaptive",
    "btn-menu-active",
    "btn-aside-active",
    "rotate-90",
    "state-bold",
    "state-light",
    "arg-container",
    "arg-container-checkbox",
  ],
  theme: {
    colors: {
      accent: "var(--alas-accent)",
      danger: "var(--alas-danger)",
      "status-idle": "var(--alas-status-idle)",
      "status-running": "var(--alas-status-running)",
      "status-warning": "var(--alas-status-warning)",
      "status-updating": "var(--alas-status-updating)",
    },
  },
  shortcuts: {
    /* ---------------- buttons ---------------- */
    // Layout-only button base. No border-color here: variants set their own
    // (a shared border-transparent would fight the variant colors in the
    // generated rule). Variants add their own colors, so conflicting hover
    // colors between .btn and .btn-* can never fight either.
    "btn-core":
      "inline-block text-center align-middle select-none border-solid " +
      "[transition:none] [padding:var(--alas-btn-py)_var(--alas-btn-px)] [font-size:var(--alas-btn-fs)] " +
      "[font-weight:var(--alas-btn-fw)] [line-height:var(--alas-btn-lh)] [font-family:var(--alas-btn-font,inherit)] " +
      "[border-width:var(--alas-btn-bw)] rounded-[var(--alas-btn-radius)] " +
      "focus:outline-none focus:shadow-none disabled:opacity-65",
    btn: "btn-core border-transparent [color:var(--alas-btn-color)] hover:[color:var(--alas-btn-hover)] hover:no-underline",
    "btn-sm": "!py-1 !px-2 ![font-size:var(--alas-btn-sm-fs)] !rounded-[var(--alas-btn-sm-radius)]",
    "btn-primary":
      "btn-core text-white [background:var(--alas-primary)] [border-color:var(--alas-primary)] " +
      "hover:[background:var(--alas-primary-hover)] hover:[border-color:var(--alas-primary-hover-border)] " +
      "active:[background:var(--alas-primary-active)] active:[border-color:var(--alas-primary-active-border)] " +
      "disabled:[background:var(--alas-primary)] disabled:[border-color:var(--alas-primary)]",
    "btn-success":
      "btn-core text-white [background:var(--alas-success)] [border-color:var(--alas-success)] " +
      "hover:[background:var(--alas-success-hover)] hover:[border-color:var(--alas-success-hover-border)] " +
      "active:[background:var(--alas-success-active)] active:[border-color:var(--alas-success-active-border)] " +
      "disabled:[background:var(--alas-success)] disabled:[border-color:var(--alas-success)]",
    "btn-info":
      "btn-core text-white [background:var(--alas-info)] [border-color:var(--alas-info)] " +
      "hover:[background:var(--alas-info-hover)] hover:[border-color:var(--alas-info-hover-border)] " +
      "active:[background:var(--alas-info-active)] active:[border-color:var(--alas-info-active-border)] " +
      "disabled:[background:var(--alas-info)] disabled:[border-color:var(--alas-info)]",
    // Neutral button visible on light and dark themes (old alas-ui.css).
    // Fixed 1px border on every theme (the old rule declared its own width).
    "btn-adaptive":
      "btn-core [color:inherit] ![border-width:1px] [border-color:#6c757d] bg-transparent " +
      "hover:[border-color:#adb5bd] hover:[background:rgba(0,0,0,.12)]",
    // Sidebar menu entry (old .btn.btn-menu)
    "btn-menu":
      "block w-full font-normal bg-transparent border-solid border-transparent border-0 border-l-3 rounded-none " +
      "[padding:.0625rem_.625rem_.0625rem_.75rem] [transition:border_.05s_ease-in-out,padding_.05s_ease-in-out] " +
      "whitespace-pre-wrap text-left hover:font-bold hover:[border-left-color:var(--alas-accent)] " +
      "hover:[color:var(--alas-accent)]",
    "btn-menu-active": "font-bold [border-left-color:var(--alas-accent)] [color:var(--alas-accent)]",
    // Instance sidebar entry (old .btn.btn-aside)
    "btn-aside":
      "w-16 text-[0.8rem] font-normal bg-transparent border-solid border-transparent border-0 border-l-4 rounded-none " +
      "[padding:.375rem_0_.75rem] mb-1.5 [transition:border_.1s_ease-in-out,padding_.1s_ease-in-out] " +
      "hover:border-l-accent hover:pl-[3px] hover:font-bold hover:text-accent",
    "btn-aside-active": "border-l-accent pl-[3px] font-bold text-accent",
    // On/off toggle (old .btn-on / .btn-off; both declare their own 1px border)
    "btn-off":
      "btn-core rounded-none m-0 ![border-width:1px] [background:var(--alas-off-bg)] [border-color:var(--alas-off-border)] " +
      "[color:var(--alas-btn-color)] hover:[color:var(--alas-btn-hover)]",
    "btn-on":
      "btn-core rounded-none m-0 ![border-width:1px] [background:var(--alas-accent)] [border-color:var(--alas-on-border)] " +
      "text-white hover:text-white",
    // Settings right-side group navigator (old .btn.btn-navigator)
    "btn-navigator":
      "btn-core border-transparent rounded-none m-0 w-full text-left [transition:color_0s_ease-in-out] " +
      "[background:var(--alas-navigator-bg)] [color:var(--alas-btn-color)] hover:font-bold hover:text-accent",
    "aside-icon":
      "block w-8 h-8 mx-auto mb-1.5 [background-color:var(--alas-icon)] " +
      "[mask:no-repeat_center_/_contain] [-webkit-mask:no-repeat_center_/_contain]",

    /* ---------------- forms ---------------- */
    "form-control":
      "block w-full bg-[var(--alas-input-bg)] border-0 rounded-[initial] [padding:.375rem_.75rem] [margin-top:.125rem] " +
      "h-auto [transition:none] [font-weight:var(--alas-input-fw,400)] [font-size:var(--alas-input-fs)] leading-6 " +
      "[color:var(--alas-input-color)] focus:outline-none focus:shadow-none focus:[background:var(--alas-input-focus-bg)]",
    "form-control-sm": "!py-1 !px-2 ![font-size:var(--alas-input-sm-fs)]",
    "form-check": "relative block pl-5",
    "form-check-input":
      "absolute [margin-top:.3rem] -ml-5 w-5 h-5 [accent-color:#7a77bb] " +
      "focus:outline-none focus:shadow-none",
    "state-display":
      "border-solid border-1 [border-color:var(--alas-muted-border)] border-b-0 px-2 h-auto overflow-hidden " +
      "[text-overflow:ellipsis] whitespace-nowrap",
    "state-bold": "font-bold [color:var(--alas-accent)]",
    "state-light": "[color:var(--alas-state-light)]",

    /* ---------------- content ---------------- */
    table:
      "w-full [margin-bottom:1rem] [color:var(--alas-table-color)] [border-collapse:collapse] " +
      "[&_th,&_td]:p-3 [&_th,&_td]:align-top [&_th,&_td]:[border-top:var(--alas-table-row-border)] " +
      "[&_th,&_td]:[background:var(--alas-table-cell-bg)] " +
      "[&_thead_th]:align-bottom [&_thead_th]:[border-bottom:var(--alas-table-thead-border)]",
    "table-sm": "[&_th,&_td]:!p-1.2",
    alert:
      "relative [padding:.75rem_1.25rem] [margin-bottom:1rem] border-solid border-transparent " +
      "[border-width:var(--alas-alert-bw)] rounded-[var(--alas-alert-radius)] " +
      "[color:var(--alas-alert-color,inherit)] [font-size:var(--alas-alert-fs,inherit)] " +
      "[font-weight:var(--alas-alert-fw,inherit)]",
    "alert-danger":
      "alert [color:var(--alas-alert-danger-color)] [background:var(--alas-alert-danger-bg)] " +
      "[border-color:var(--alas-alert-danger-border)]",
    "text-muted": "![color:var(--alas-text-muted)]",
    "text-success": "![color:var(--alas-text-success)]",
    "text-danger": "![color:var(--alas-text-danger)]",
    "spinner-border":
      "inline-block w-8 h-8 [vertical-align:-.125em] rounded-full border-solid " +
      "[border:.25em_solid_currentColor] [border-right-color:transparent] " +
      "[animation:spinner-border_.75s_linear_infinite]",
    "spinner-border-sm":
      "inline-block w-4 h-4 [vertical-align:-.125em] rounded-full border-solid " +
      "[border:.2em_solid_currentColor] [border-right-color:transparent] " +
      "[animation:spinner-border_.75s_linear_infinite]",

    /* ---------------- header ---------------- */
    "header-state-dot": "w-2 h-2 rounded-full bg-status-idle",
    "header-state-inactive": "[&_.header-state-dot]:bg-status-idle",
    "header-state-running": "[&_.header-state-dot]:bg-status-running",
    "header-state-warning": "[&_.header-state-dot]:bg-status-warning",
    "header-state-updating": "[&_.header-state-dot]:bg-status-updating",

    /* ---------------- logs ---------------- */
    "log-view":
      "grow min-h-0 m-1.25 p-2.5 overflow-y-auto leading-[1.2] text-[0.85rem] " +
      "[font-family:Menlo,consolas,'DejaVu_Sans_Mono','Courier_New',monospace] whitespace-pre [color:inherit] " +
      "[background:var(--alas-shell-panel)] border-solid border-1 [border-color:var(--alas-shell-border)]",
    "tool-log":
      "[grid-column:2] [margin:.3rem_0] min-h-60 max-h-[40vh] overflow-y-auto [background:var(--alas-log-bg)] " +
      "[color:var(--alas-log-fg)] p-2 [font-size:12px] rounded [white-space:pre-wrap]",

    /* ---------------- misc shell pieces ---------------- */
    "hr-group": "my-1 [border:0] ![border-top:var(--alas-hr-border)] [background:var(--alas-hr-bg)]",
    "hr-task-group-box": "flex items-center mb-2",
    "hr-task-group-line": "grow [border-top:.125rem_solid_var(--alas-task-line)]",
    "hr-task-group-text": "mx-2 text-[0.875rem] [color:var(--alas-task-text)]",
    "arg-title": "text-base font-medium mx-1 [overflow-wrap:break-word]",
    "arg-help":
      "text-[0.8rem] mx-1 [margin-top:.2rem] [margin-bottom:.1rem] [overflow-wrap:break-word] [color:var(--alas-help)]",
    "arg-container": "grid [margin:.125rem_0]",
    "arg-container-checkbox": "grid [margin:.375rem_0]",
    "overview-notask-text": "text-center text-[0.875rem] [color:darkgrey]",
    "group-card":
      "my-2 p-4 [background:var(--alas-shell-panel)] border-solid border-1 [border-color:var(--alas-shell-border)]",
    "group-card-title": "text-[1.25rem] font-medium mx-1",
    "group-card-help":
      "text-[0.8rem] mx-1 [margin-top:.2rem] [margin-bottom:.1rem] [overflow-wrap:break-word] [color:var(--alas-help)]",
    "scheduler-bar":
      "flex items-center justify-between font-medium m-1.25 p-2.5 [background:var(--alas-shell-panel)] " +
      "border-solid border-1 [border-color:var(--alas-shell-border)]",
    "log-bar": "scheduler-bar",
    "running-section":
      "grid [grid-auto-flow:row] [grid-template-rows:auto_auto_1fr] font-medium m-1.25 p-2.5 " +
      "[background:var(--alas-shell-panel)] border-solid border-1 [border-color:var(--alas-shell-border)] " +
      "h-31 flex-shrink-0 overflow-y-auto",
    "pending-section":
      "grid [grid-auto-flow:row] [grid-template-rows:auto_auto_1fr] font-medium m-1.25 p-2.5 " +
      "[background:var(--alas-shell-panel)] border-solid border-1 [border-color:var(--alas-shell-border)] " +
      "min-h-31 max-h-52 flex-shrink-0 overflow-y-auto",
    "waiting-section":
      "grid [grid-auto-flow:row] [grid-template-rows:auto_auto_1fr] font-medium m-1.25 p-2.5 " +
      "[background:var(--alas-shell-panel)] border-solid border-1 [border-color:var(--alas-shell-border)] " +
      "min-h-31 grow flex-shrink overflow-y-auto",
    "running-section-title": "text-[1.25rem] font-medium mx-2.5",
    "pending-section-title": "text-[1.25rem] font-medium mx-2.5",
    "waiting-section-title": "text-[1.25rem] font-medium mx-2.5",
    "running-tasks": "overflow-y-auto h-full",
    "pending-tasks": "overflow-y-auto h-full",
    "waiting-tasks": "overflow-y-auto h-full",
    "overview-task":
      "grid [grid-auto-flow:column] [grid-template-columns:1fr_auto] [margin:.125rem_.625rem_.125rem_.375rem]",
    "log-bar-btns": "grid [grid-auto-flow:column]",
  },
});
