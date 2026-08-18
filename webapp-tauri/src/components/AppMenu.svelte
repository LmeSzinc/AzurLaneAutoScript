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

<nav class="app-menu">
  <button
    class="btn btn-menu"
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
      <div class="menu-collapse">
        <button class="menu-collapse-title" onclick={() => toggleGroup(group.name)}>
          <span class="collapse-arrow" class:collapse-arrow-open={isGroupOpen(group.name)}>&#x25B8;</span>
          {t(`Menu.${group.name}.name`)}
        </button>
        {#if isGroupOpen(group.name)}
          <div class="menu-collapse-body">
            {#each group.tasks as task (task)}
              <button class="btn btn-menu" class:btn-menu-active={activeTask === task} onclick={() => selectTask(task)}>
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
        <button class="btn btn-menu" class:btn-menu-active={activeTask === task} onclick={() => selectTask(task)}>
          {t(`Task.${task}.name`)}
        </button>
      {/each}
    {/if}
  {/each}
</nav>

<style>
  .app-menu {
    z-index: 90;
    padding-left: 0.5rem;
    padding-right: 0.5rem;
    padding-top: 1.2rem;
    overflow-y: auto;
    width: 12rem;
    flex-shrink: 0;
  }
  .app-menu .btn-menu {
    display: block;
    width: 100%;
    /* original gap between menu buttons */
    margin-bottom: 8px;
  }
  .menu-collapse-title {
    display: block;
    width: 100%;
    font-weight: 500;
    background-color: transparent;
    border: 0;
    text-align: left;
    padding: 8px 12px;
    cursor: pointer;
  }
  .menu-collapse-title:hover {
    font-weight: bold;
  }
  .collapse-arrow {
    display: inline-block;
    transition: transform 0.15s ease;
    margin-right: 2px;
  }
  .collapse-arrow-open {
    transform: rotate(90deg);
  }
  .menu-collapse-body {
    margin-left: 0.625rem;
  }
</style>
