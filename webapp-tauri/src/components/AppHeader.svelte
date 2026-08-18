<script lang="ts">
import { invoke } from "@tauri-apps/api/core";
import { t } from "../api/i18n.svelte";
import { status, titleState } from "../api/store.svelte";
import { route } from "../router.svelte";

const isTauri = "__TAURI_INTERNALS__" in window;

const stateText = $derived.by(() => {
  const state = status.instances[0]?.state ?? 0;
  if (state === 1) return t("Gui.Status.Running");
  if (state === 3) return t("Gui.Status.Warning");
  if (state === 4) return t("Gui.Status.Updating");
  return t("Gui.Status.Inactive");
});

const stateClass = $derived.by(() => {
  const state = status.instances[0]?.state ?? 0;
  if (state === 1) return "header-state-running";
  if (state === 3) return "header-state-warning";
  if (state === 4) return "header-state-updating";
  return "header-state-inactive";
});

const pageTitleText = $derived.by(() => {
  if (titleState.value) return titleState.value;
  if (route.path === "/settings") {
    const task = route.query.task ?? "";
    return task ? t(`Task.${task}.name`) : "";
  }
  if (route.path === "/develop") return t("Gui.Aside.Home");
  if (route.path === "/manage") return t("Gui.AppManage.PageTitle");
  return t("Gui.MenuAlas.Overview");
});

function min() {
  void invoke("window_min");
}
function max() {
  void invoke("window_max");
}
function close() {
  void invoke("window_close");
}
</script>

<header
  class="app-header grid [grid-auto-flow:column] [grid-template-columns:4.4rem_4rem_auto_1fr_auto] items-center h-[50px] select-none [-webkit-app-region:drag] [background:var(--alas-header-bg)] [box-shadow:var(--alas-header-shadow)] [border-bottom:var(--alas-header-border-bottom)]"
>
  <img class="w-[42px] h-[42px] my-1 mx-auto rounded-3xl" src="icon/alas.png" alt="Alas" />
  <span class="text-[1.5rem] font-bold m-auto">Alas</span>
  <span class="flex items-center gap-1 text-[0.85rem] m-auto {stateClass}">
    <span class="header-state-dot"></span>
    {stateText}
  </span>
  <div class="m-auto">
    <span class="text-[1.2rem] m-auto overflow-hidden text-center whitespace-nowrap">{pageTitleText}</span>
  </div>
  {#if isTauri}
    <div class="flex h-full [-webkit-app-region:no-drag]">
      <button
        class="w-11 h-full border-0 bg-transparent text-xs cursor-pointer hover:[background:rgba(255,255,255,.08)]"
        title="Minimize"
        onclick={min}
      >
        &#x2212;
      </button>
      <button
        class="w-11 h-full border-0 bg-transparent text-xs cursor-pointer hover:[background:rgba(255,255,255,.08)]"
        title="Maximize"
        onclick={max}
      >
        &#x25A1;
      </button>
      <button
        class="w-11 h-full border-0 bg-transparent text-xs cursor-pointer hover:[background:var(--alas-danger)] hover:text-white"
        title="Close"
        onclick={close}
      >
        &#x2715;
      </button>
    </div>
  {/if}
</header>
