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

// Dot color for the instance state; classes live in the uno safelist.
const stateClass = $derived.by(() => {
  const state = status.instances[0]?.state ?? 0;
  if (state === 1) return "bg-status-running";
  if (state === 3) return "bg-status-warning";
  if (state === 4) return "bg-status-updating";
  return "bg-status-idle";
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
  class="grid h-[var(--h-header)] select-none items-center [grid-auto-flow:column] [grid-template-columns:4.4rem_4rem_auto_1fr_auto] [-webkit-app-region:drag] [background:var(--header-bg)] [box-shadow:var(--header-shadow)] [border-bottom:var(--header-line)]"
>
  <img class="mx-auto my-1 h-[42px] w-[42px] rounded-3xl" src="icon/alas.png" alt="Alas" />
  <span class="m-auto text-[1.5rem] font-bold">Alas</span>
  <span class="m-auto flex items-center gap-1 text-[0.85rem]">
    <span class="h-2 w-2 rounded-full {stateClass}"></span>
    {stateText}
  </span>
  <div class="m-auto">
    <span class="m-auto overflow-hidden text-center text-[1.2rem] whitespace-nowrap">{pageTitleText}</span>
  </div>
  {#if isTauri}
    <div class="flex h-full [-webkit-app-region:no-drag]">
      <button
        class="h-full w-11 cursor-pointer border-0 bg-transparent text-xs hover:bg-white/8"
        title="Minimize"
        onclick={min}
      >
        &#x2212;
      </button>
      <button
        class="h-full w-11 cursor-pointer border-0 bg-transparent text-xs hover:bg-white/8"
        title="Maximize"
        onclick={max}
      >
        &#x25A1;
      </button>
      <button
        class="h-full w-11 cursor-pointer border-0 bg-transparent text-xs hover:bg-danger hover:text-white"
        title="Close"
        onclick={close}
      >
        &#x2715;
      </button>
    </div>
  {/if}
</header>
