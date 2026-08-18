<script lang="ts">
import { api } from "../api/client";
import { loadI18n, t } from "../api/i18n.svelte";
import { collapsedGroups } from "../api/store.svelte";
import type { MenuSchema } from "../api/types";

let {
  onoverview,
  ontask,
}: {
  onoverview?: () => void;
  ontask?: (task: string) => void;
} = $props();

let menu = $state<MenuSchema>({});
let activeTask = $state("");

function toggleGroup(name: string) {
  collapsedGroups[name] = !collapsedGroups[name];
}

function isGroupOpen(name: string): boolean {
  return collapsedGroups[name] === true;
}

const groups = $derived.by(() => {
  const result: { name: string; collapse: boolean; tasks: string[] }[] = [];
  for (const [name, data] of Object.entries(menu)) {
    result.push({
      name,
      collapse: data.menu === "collapse",
      tasks: data.tasks ?? [],
    });
  }
  return result;
});

function selectTask(task: string) {
  activeTask = task;
  ontask?.(task);
}

$effect(() => {
  void api.schema("alas").then((schema) => {
    menu = schema.menu;
  });
  void loadI18n();
});
</script>

<nav
  class="[z-index:90] px-2 pt-[1.2rem] overflow-y-auto w-48 flex-shrink-0 [background:var(--alas-menu-bg)] [box-shadow:var(--alas-menu-shadow)] [border-right:var(--alas-menu-border-right)]"
>
  <button
    class="btn-menu mb-2"
    class:btn-menu-active={activeTask === ''}
    onclick={() => {
      activeTask = ''
      onoverview?.()
    }}
  >
    {t('Gui.MenuAlas.Overview')}
  </button>

  {#each groups as group (group.name)}
    {#if group.collapse}
      <div>
        <button
          class="block w-full font-medium bg-transparent border-0 text-left px-3 py-2 cursor-pointer hover:font-bold"
          onclick={() => toggleGroup(group.name)}
        >
          <span class="inline-block [transition:transform_.15s_ease] mr-0.5" class:rotate-90={isGroupOpen(group.name)}>
            &#x25B8;
          </span>
          {t(`Menu.${group.name}.name`)}
        </button>
        {#if isGroupOpen(group.name)}
          <div class="ml-2.5">
            {#each group.tasks as task (task)}
              <button class="btn-menu mb-2" class:btn-menu-active={activeTask === task} onclick={() => selectTask(task)}>
                {t(`Task.${task}.name`)}
              </button>
            {/each}
          </div>
        {/if}
      </div>
    {:else}
      <div class="hr-task-group-box">
        <span class="hr-task-group-line"></span>
        <span class="hr-task-group-text">{t(`Menu.${group.name}.name`)}</span>
        <span class="hr-task-group-line"></span>
      </div>
      {#each group.tasks as task (task)}
        <button class="btn-menu mb-2" class:btn-menu-active={activeTask === task} onclick={() => selectTask(task)}>
          {t(`Task.${task}.name`)}
        </button>
      {/each}
    {/if}
  {/each}
</nav>
