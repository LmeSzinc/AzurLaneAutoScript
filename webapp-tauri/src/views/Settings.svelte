<script lang="ts">
import { api } from "../api/client";
import { loadI18n, t } from "../api/i18n.svelte";
import { logs, refreshStatus, status } from "../api/store.svelte";
import type { ArgDefinition } from "../api/types";
import AppAside from "../components/AppAside.svelte";
import AppMenu from "../components/AppMenu.svelte";
import DynamicForm from "../components/DynamicForm.svelte";
import LogView from "../components/LogView.svelte";
import { push, replace, route } from "../router.svelte";

let selectedTask = $state("");
let schema = $state<Record<string, Record<string, Record<string, ArgDefinition>>>>({});
let config = $state<Record<string, unknown>>({});
const activeInstance = $derived(status.instances[0]?.name ?? "alas");
const EMPTY_LOGS: string[] = [];
let saving = $state(false);
/** Tasks whose page is 'tool' show a status view instead of the form */
let toolTasks = $state<Set<string>>(new Set());
let toolAlive = $state(false);
let toolKeepBottom = $state(true);

const isToolTask = $derived(toolTasks.has(selectedTask));

async function loadTask(task: string) {
  selectedTask = task;
  const { menu, args } = await api.schema("alas");
  const found = new Set(toolTasks);
  for (const data of Object.values(menu)) {
    if (data.page === "tool") {
      for (const name of data.tasks ?? []) {
        found.add(name);
      }
    }
  }
  toolTasks = found;
  schema = args;
  config = await api.config(activeInstance);
}

async function refreshToolState() {
  if (isToolTask && activeInstance) {
    const sched = await api.scheduler(activeInstance);
    toolAlive = sched.alive;
  }
}

async function toggleTool() {
  if (toolAlive) {
    await api.stop(activeInstance);
  } else {
    await api.run(activeInstance);
  }
  await refreshToolState();
}

/** Group names shown in the right navigator. */
const navigatorGroups = $derived(Object.keys(schema[selectedTask] ?? {}).filter((name) => name !== "Storage"));

function scrollToGroup(name: string) {
  document.getElementById(`group-${name}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function saveValue(path: string, value: unknown) {
  saving = true;
  try {
    await api.saveConfig(activeInstance, { [path]: value });
    config = await api.config(activeInstance);
  } finally {
    saving = false;
  }
}

function onAsideSelect(name: string) {
  if (name === "Home") {
    push("/develop");
    return;
  }
  if (name === "Manage") {
    push("/manage");
    return;
  }
  push("/");
}

function onMenuTask(task: string) {
  replace("/settings", { task });
}

$effect(() => {
  const task = route.query.task || "Alas";
  if (task !== selectedTask || Object.keys(schema).length === 0) {
    void loadTask(task).then(() => refreshToolState());
  }
});

$effect(() => {
  void loadI18n();
  void refreshStatus();
});
</script>

<div class="flex h-full overflow-hidden bg-surface-app">
  <AppAside active={activeInstance} onselect={onAsideSelect} />
  <AppMenu onoverview={() => push('/')} ontask={onMenuTask} />

  <div class="min-w-0 grow overflow-y-auto bg-surface-app p-4">
    {#if isToolTask}
      <!-- tool tasks: scheduler bar (top) + form + log (bottom) -->
      <div class="grid gap-1.6 [grid-auto-flow:column] [grid-template-columns:1fr_minmax(25rem,6fr)_1fr]">
        <div class="panel col-[2] my-[0.3rem] flex items-center gap-2 p-2.4">
          <span>{t('Gui.Overview.Scheduler')}</span>
          <button
            class="btn m-0 rounded-none border-toggle"
            class:bg-accent={!toolAlive}
            class:bg-surface-app={toolAlive}
            class:text-white={!toolAlive}
            class:text-body={toolAlive}
            onclick={toggleTool}
          >
            {toolAlive ? t('Gui.Button.Stop') : t('Gui.Button.Start')}
          </button>
          <span class="ms-auto">{t('Gui.Overview.Log')}</span>
          <button
            class="btn m-0 rounded-none border-toggle"
            class:bg-accent={toolKeepBottom}
            class:bg-surface-app={!toolKeepBottom}
            class:text-white={toolKeepBottom}
            class:text-body={!toolKeepBottom}
            onclick={() => (toolKeepBottom = !toolKeepBottom)}
          >
            {toolKeepBottom ? t('Gui.Button.ScrollON') : t('Gui.Button.ScrollOFF')}
          </button>
        </div>

        {#each Object.entries(schema[selectedTask] ?? {}) as [groupKey, groupArgs] (groupKey)}
          {#if groupKey !== 'Storage'}
            <div class="panel col-[2] my-2 border-0 p-4" id={`group-${groupKey}`}>
              <div class="mx-1 text-[1.25rem] font-medium">{t(`${groupKey}._info.name`)}</div>
              {#if t(`${groupKey}._info.help`) !== `${groupKey}._info.help`}
                <div class="mx-1 mt-[0.2rem] mb-[0.1rem] text-[0.8rem] text-muted [overflow-wrap:break-word]">
                  {t(`${groupKey}._info.help`)}
                </div>
              {/if}
              <hr class="my-1 border-0 bg-surface-hr [border-top:var(--hr-line)]" />
              <DynamicForm args={groupArgs} group={groupKey} task={selectedTask} {config} onsave={saveValue} />
            </div>
          {/if}
        {/each}

        <LogView
          class="col-[2] my-[0.3rem] min-h-60 max-h-[40vh] overflow-y-auto rounded bg-surface-log p-2 text-xs whitespace-pre-wrap [color:var(--log-fg)]"
          lines={logs[activeInstance] ?? EMPTY_LOGS}
          keepBottom={toolKeepBottom}
        />
      </div>
    {:else}
      {#if selectedTask && t(`Task.${selectedTask}.help`) !== `Task.${selectedTask}.help`}
        <p class="mt-0 mb-4 text-muted">{t(`Task.${selectedTask}.help`)}</p>
      {/if}
      {#each Object.entries(schema[selectedTask] ?? {}) as [groupKey, groupArgs] (groupKey)}
        {#if groupKey !== 'Storage'}
          <div class="panel my-2 p-4" id={`group-${groupKey}`}>
            <div class="mx-1 text-[1.25rem] font-medium">{t(`${groupKey}._info.name`)}</div>
            {#if t(`${groupKey}._info.help`) !== `${groupKey}._info.help`}
              <div class="mx-1 mt-[0.2rem] mb-[0.1rem] text-[0.8rem] text-muted [overflow-wrap:break-word]">
                {t(`${groupKey}._info.help`)}
              </div>
            {/if}
            <hr class="my-1 border-0 bg-surface-hr [border-top:var(--hr-line)]" />
            <DynamicForm args={groupArgs} group={groupKey} task={selectedTask} {config} onsave={saveValue} />
          </div>
        {/if}
      {/each}
      {#if saving}
        <span class="text-xs text-status-running">saving...</span>
      {/if}
    {/if}
  </div>

  <!-- right navigator: group anchors -->
  {#if navigatorGroups.length}
    <nav
      class="mx-4 my-2 max-w-60 min-w-28 flex-shrink-0 overflow-y-auto border border-solid border-line-panel bg-surface-panel text-body [height:min-content] [width:max-content]"
    >
      {#each navigatorGroups as name (name)}
        <button
          class="btn w-full justify-start rounded-none border-transparent bg-transparent text-body transition-none hover:font-bold hover:text-accent"
          onclick={() => scrollToGroup(name)}
        >
          {t(`${name}._info.name`)}
        </button>
      {/each}
    </nav>
  {/if}
</div>
