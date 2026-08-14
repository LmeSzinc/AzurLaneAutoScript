<script lang="ts">
  import { api } from '../api/client'
  import { loadI18n, t } from '../api/i18n.svelte'
  import { logs, refreshStatus, status } from '../api/store.svelte'
  import { push, replace, route } from '../router.svelte'
  import type { ArgDefinition } from '../api/types'
  import AppAside from '../components/AppAside.svelte'
  import AppMenu from '../components/AppMenu.svelte'
  import DynamicForm from '../components/DynamicForm.svelte'

  let selectedTask = $state('')
  let schema = $state<Record<string, Record<string, Record<string, ArgDefinition>>>>({})
  let config = $state<Record<string, unknown>>({})
  const activeInstance = $derived(status.instances[0]?.name ?? 'alas')
  let saving = $state(false)
  /** Tasks whose page is 'tool' show a status view instead of the form */
  let toolTasks = $state<Set<string>>(new Set())
  let toolAlive = $state(false)
  let toolKeepBottom = $state(true)
  let toolLogEl = $state<HTMLElement | null>(null)

  const isToolTask = $derived(toolTasks.has(selectedTask))

  async function loadTask(task: string) {
    selectedTask = task
    const { menu, args } = await api.schema('alas')
    const found = new Set(toolTasks)
    for (const data of Object.values(menu)) {
      if (data.page === 'tool') {
        for (const name of data.tasks ?? []) {
          found.add(name)
        }
      }
    }
    toolTasks = found
    schema = args
    config = await api.config(activeInstance)
  }

  async function refreshToolState() {
    if (isToolTask && activeInstance) {
      const sched = await api.scheduler(activeInstance)
      toolAlive = sched.alive
    }
  }

  async function toggleTool() {
    if (toolAlive) {
      await api.stop(activeInstance)
    } else {
      await api.run(activeInstance)
    }
    await refreshToolState()
  }

  /** Group names shown in the right navigator. */
  const navigatorGroups = $derived(
    Object.keys(schema[selectedTask] ?? {}).filter((name) => name !== 'Storage'),
  )

  function scrollToGroup(name: string) {
    document.getElementById(`group-${name}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  async function saveValue(path: string, value: unknown) {
    saving = true
    try {
      await api.saveConfig(activeInstance, { [path]: value })
      config = await api.config(activeInstance)
    } finally {
      saving = false
    }
  }

  function onAsideSelect(name: string) {
    if (name === 'Home') {
      push('/develop')
      return
    }
    if (name === 'Manage') {
      push('/manage')
      return
    }
    push('/')
  }

  function onMenuTask(task: string) {
    replace('/settings', { task })
  }

  $effect(() => {
    const task = route.query.task || 'Alas'
    if (task !== selectedTask || Object.keys(schema).length === 0) {
      void loadTask(task).then(() => refreshToolState())
    }
  })

  $effect(() => {
    void loadI18n()
    void refreshStatus()
  })

  // Auto-scroll the tool log view
  $effect(() => {
    void logs[activeInstance]?.length
    if (toolKeepBottom && toolLogEl) {
      toolLogEl.scrollTop = toolLogEl.scrollHeight
    }
  })
</script>

<div class="settings-wrap">
  <AppAside active={activeInstance} onselect={onAsideSelect} />
  <AppMenu onoverview={() => push('/')} ontask={onMenuTask} />

  <div class="content">
    {#if selectedTask}
      <h4>{t(`Task.${selectedTask}.name`)}</h4>
    {/if}

    {#if isToolTask}
      <!-- tool tasks: scheduler bar (top) + form + log (bottom) -->
      <div class="tool-view">
        <div class="tool-bar">
          <span class="col-title">{t('Gui.Overview.Scheduler')}</span>
          <button
            class="btn btn-sm"
            class:btn-off={toolAlive}
            class:btn-on={!toolAlive}
            onclick={toggleTool}
          >
            {toolAlive ? t('Gui.Button.Stop') : t('Gui.Button.Start')}
          </button>
          <span class="col-title ms-auto">{t('Gui.Overview.Log')}</span>
          <button
            class="btn btn-sm btn-adaptive"
            onclick={() => (toolKeepBottom = !toolKeepBottom)}
          >
            {toolKeepBottom ? t('Gui.Button.ScrollON') : t('Gui.Button.ScrollOFF')}
          </button>
        </div>

        {#each Object.entries(schema[selectedTask] ?? {}) as [groupKey, groupArgs] (groupKey)}
          {#if groupKey !== 'Storage'}
            <div class="group-card" id={`group-${groupKey}`}>
              <div class="group-card-title">{t(`${groupKey}._info.name`)}</div>
              {#if t(`${groupKey}._info.help`) !== `${groupKey}._info.help`}
                <div class="group-card-help">{t(`${groupKey}._info.help`)}</div>
              {/if}
              <hr class="hr-group" />
              <DynamicForm
                args={groupArgs}
                group={groupKey}
                task={selectedTask}
                config={config}
                onsave={saveValue}
              />
            </div>
          {/if}
        {/each}

        <pre class="tool-log" bind:this={toolLogEl}><code>{(logs[activeInstance] ?? []).join('\n')}</code></pre>
      </div>
    {:else}
      {#if selectedTask && t(`Task.${selectedTask}.help`) !== `Task.${selectedTask}.help`}
        <p class="text-muted">{t(`Task.${selectedTask}.help`)}</p>
      {/if}
      {#each Object.entries(schema[selectedTask] ?? {}) as [groupKey, groupArgs] (groupKey)}
        {#if groupKey !== 'Storage'}
          <div class="group-card" id={`group-${groupKey}`}>
            <div class="group-card-title">{t(`${groupKey}._info.name`)}</div>
            {#if t(`${groupKey}._info.help`) !== `${groupKey}._info.help`}
              <div class="group-card-help">{t(`${groupKey}._info.help`)}</div>
            {/if}
            <hr class="hr-group" />
            <DynamicForm
              args={groupArgs}
              group={groupKey}
              task={selectedTask}
              config={config}
              onsave={saveValue}
            />
          </div>
        {/if}
      {/each}
      {#if saving}
        <span class="saving-hint">saving...</span>
      {/if}
    {/if}
  </div>

  <!-- right navigator: group anchors -->
  {#if navigatorGroups.length}
    <nav class="navigator">
      {#each navigatorGroups as name (name)}
        <button class="btn btn-sm btn-navigator" onclick={() => scrollToGroup(name)}>
          {t(`${name}._info.name`)}
        </button>
      {/each}
    </nav>
  {/if}
</div>

<style>
  .settings-wrap {
    height: 100%;
    display: flex;
    overflow: hidden;
  }
  .content {
    flex-grow: 1;
    padding: 1rem;
    overflow-y: auto;
  }
  .tool-bar {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0.3rem 0;
    padding: 0.6rem;
  }
  .tool-bar .col-title {
    font-size: 1.25rem;
  }
  .tool-log {
    flex-grow: 1;
    margin: 0.3rem 0;
    min-height: 160px;
    max-height: 40vh;
    overflow-y: auto;
    background: #16191d;
    color: #d4d9de;
    padding: 8px;
    font-size: 12px;
    border-radius: 4px;
    white-space: pre-wrap;
  }
  .saving-hint {
    font-size: 12px;
    color: #4cd07d;
  }
  .navigator {
    margin: 0.5rem 1rem;
    height: min-content;
    max-width: 15rem;
    flex-shrink: 0;
    overflow-y: auto;
  }
</style>
