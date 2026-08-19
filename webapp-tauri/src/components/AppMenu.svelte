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
  class="w-48 flex-shrink-0 overflow-y-auto bg-surface-panel px-2 pt-[1.2rem] [z-index:90] [box-shadow:var(--menu-shadow)] [border-right:var(--menu-line)]"
>
  <button
    class="mb-2 block w-full rounded-none border-0 border-l-3 border-solid border-transparent bg-transparent px-3 py-[1px] text-left font-normal whitespace-pre-wrap [transition:border_.05s_ease-in-out,padding_.05s_ease-in-out] hover:border-l-accent hover:font-bold hover:text-accent"
    class:border-l-accent={activeTask === ''}
    class:font-bold={activeTask === ''}
    class:text-accent={activeTask === ''}
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
          class="block w-full cursor-pointer border-0 bg-transparent px-3 py-2 text-left font-medium hover:font-bold"
          onclick={() => toggleGroup(group.name)}
        >
          <span class="mr-0.5 inline-block [transition:transform_.15s_ease]" class:rotate-90={isGroupOpen(group.name)}>
            &#x25B8;
          </span>
          {t(`Menu.${group.name}.name`)}
        </button>
        {#if isGroupOpen(group.name)}
          <div class="ml-2.5">
            {#each group.tasks as task (task)}
              <button
                class="mb-2 block w-full rounded-none border-0 border-l-3 border-solid border-transparent bg-transparent px-3 py-[1px] text-left font-normal whitespace-pre-wrap [transition:border_.05s_ease-in-out,padding_.05s_ease-in-out] hover:border-l-accent hover:font-bold hover:text-accent"
                class:border-l-accent={activeTask === task}
                class:font-bold={activeTask === task}
                class:text-accent={activeTask === task}
                onclick={() => selectTask(task)}
              >
                {t(`Task.${task}.name`)}
              </button>
            {/each}
          </div>
        {/if}
      </div>
    {:else}
      <div class="mb-2 flex items-center">
        <span class="grow [border-top:.125rem_solid_var(--line-task)]"></span>
        <span class="mx-2 text-[0.875rem] text-muted">{t(`Menu.${group.name}.name`)}</span>
        <span class="grow [border-top:.125rem_solid_var(--line-task)]"></span>
      </div>
      {#each group.tasks as task (task)}
        <button
          class="mb-2 block w-full rounded-none border-0 border-l-3 border-solid border-transparent bg-transparent px-3 py-[1px] text-left font-normal whitespace-pre-wrap [transition:border_.05s_ease-in-out,padding_.05s_ease-in-out] hover:border-l-accent hover:font-bold hover:text-accent"
          class:border-l-accent={activeTask === task}
          class:font-bold={activeTask === task}
          class:text-accent={activeTask === task}
          onclick={() => selectTask(task)}
        >
          {t(`Task.${task}.name`)}
        </button>
      {/each}
    {/if}
  {/each}
</nav>
