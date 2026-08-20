<script lang="ts">
import { t } from "../api/i18n.svelte";
import { status, titleState } from "../api/store.svelte";
import { route } from "../router.svelte";

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
</script>

<!-- Branding/status bar only: window controls are the native title bar
     (decorations: true in tauri.conf.json), so no Tauri IPC lives here. -->
<header
  class="grid h-[var(--h-header)] select-none items-center [grid-auto-flow:column] [grid-template-columns:4.4rem_4rem_auto_1fr] [background:var(--header-bg)] [box-shadow:var(--header-shadow)] [border-bottom:var(--header-line)]"
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
</header>
