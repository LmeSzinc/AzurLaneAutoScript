<script lang="ts">
  import { api } from '../api/client'
  import { t, loadI18n } from '../api/i18n.svelte'
  import { logs, refreshStatus, status } from '../api/store.svelte'
  import { push } from '../router.svelte'
  import AppAside from '../components/AppAside.svelte'
  import AppMenu from '../components/AppMenu.svelte'

  interface SchedulerTask {
    command: string
    next_run: string
  }

  let scheduler = $state<{
    alive: boolean
    running: SchedulerTask[]
    pending: SchedulerTask[]
    waiting: SchedulerTask[]
  }>({ alive: false, running: [], pending: [], waiting: [] })

  const activeInstance = $derived(status.instances[0]?.name ?? 'alas')
  let keepBottom = $state(true)
  let logEl = $state<HTMLElement | null>(null)

  async function refreshScheduler() {
    if (!activeInstance) return
    scheduler = await api.scheduler(activeInstance)
  }

  async function toggleScheduler() {
    if (scheduler.alive) {
      await api.stop(activeInstance)
    } else {
      await api.run(activeInstance)
    }
    await refreshStatus()
    await refreshScheduler()
  }

  function goSettings(task: string) {
    push('/settings', { task })
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
    // instance: stay on the overview page
    push('/')
  }

  // Auto-scroll the log view when keepBottom is on
  function scrollLog() {
    if (keepBottom && logEl) {
      logEl.scrollTop = logEl.scrollHeight
    }
  }

  $effect(() => {
    void loadI18n()
    void refreshScheduler()
    const timer = window.setInterval(() => {
      void refreshStatus()
      void refreshScheduler()
      scrollLog()
    }, 5000)
    return () => window.clearInterval(timer)
  })

  // Scroll as soon as new logs arrive over the websocket
  $effect(() => {
    void logs[activeInstance]?.length
    scrollLog()
  })
</script>

<div class="home">
  <AppAside active={activeInstance} onselect={onAsideSelect} />
  <AppMenu
    onoverview={() => push('/')}
    ontask={(task) => goSettings(task)}
  />

  <div class="content overview">
    <!-- schedulers column -->
    <section class="scheduler-col">
      <div class="scheduler-bar">
        <span class="bar-title">{t('Gui.Overview.Scheduler')}</span>
        <button
          class="btn btn-sm"
          class:btn-off={scheduler.alive}
          class:btn-on={!scheduler.alive}
          onclick={toggleScheduler}
        >
          {scheduler.alive ? t('Gui.Button.Stop') : t('Gui.Button.Start')}
        </button>
      </div>

      <div class="running-section">
        <div class="running-section-title">{t('Gui.Overview.Running')}</div>
        <hr class="hr-group" />
        <div class="running-tasks">
          {#if scheduler.running.length === 0}
            <div class="overview-notask-text">{t('Gui.Overview.NoTask')}</div>
          {/if}
          {#each scheduler.running as task (task.command)}
            <div class="overview-task">
              <div>
                <div class="arg-title">{t(`Task.${task.command}.name`)}</div>
                <div class="arg-help">{task.next_run}</div>
              </div>
              <button class="btn btn-sm btn-adaptive" onclick={() => goSettings(task.command)}>
                {t('Gui.Button.Setting')}
              </button>
            </div>
          {/each}
        </div>
      </div>

      <div class="pending-section">
        <div class="pending-section-title">{t('Gui.Overview.Pending')}</div>
        <hr class="hr-group" />
        <div class="pending-tasks">
          {#if scheduler.pending.length === 0}
            <div class="overview-notask-text">{t('Gui.Overview.NoTask')}</div>
          {/if}
          {#each scheduler.pending as task (task.command)}
            <div class="overview-task">
              <div>
                <div class="arg-title">{t(`Task.${task.command}.name`)}</div>
                <div class="arg-help">{task.next_run}</div>
              </div>
              <button class="btn btn-sm btn-adaptive" onclick={() => goSettings(task.command)}>
                {t('Gui.Button.Setting')}
              </button>
            </div>
          {/each}
        </div>
      </div>

      <div class="waiting-section">
        <div class="waiting-section-title">{t('Gui.Overview.Waiting')}</div>
        <hr class="hr-group" />
        <div class="waiting-tasks">
          {#if scheduler.waiting.length === 0}
            <div class="overview-notask-text">{t('Gui.Overview.NoTask')}</div>
          {/if}
          {#each scheduler.waiting as task (task.command)}
            <div class="overview-task">
              <div>
                <div class="arg-title">{t(`Task.${task.command}.name`)}</div>
                <div class="arg-help">{task.next_run}</div>
              </div>
              <button class="btn btn-sm btn-adaptive" onclick={() => goSettings(task.command)}>
                {t('Gui.Button.Setting')}
              </button>
            </div>
          {/each}
        </div>
      </div>
    </section>

    <!-- logs column -->
    <section class="log-col">
      <div class="log-bar">
        <span class="bar-title">{t('Gui.Overview.Log')}</span>
        <div class="log-bar-btns">
          <button class="btn btn-sm" class:btn-on={keepBottom} class:btn-off={!keepBottom} onclick={() => (keepBottom = !keepBottom)}>
            {keepBottom ? t('Gui.Button.ScrollON') : t('Gui.Button.ScrollOFF')}
          </button>
        </div>
      </div>
      <pre class="log-view" bind:this={logEl}><code>{(logs[activeInstance] ?? []).join('\n')}</code></pre>
    </section>
  </div>
</div>

<style>
  .home {
    height: 100%;
    display: flex;
    overflow: hidden;
  }
  .content {
    flex-grow: 1;
    min-width: 0;
    padding: 0.625rem;
    /* original overview grid: schedulers minmax(16rem,20rem) + logs minmax(24rem,1fr) */
    grid-template-columns: minmax(16rem, 20rem) minmax(24rem, 1fr);
    gap: 0.625rem;
    overflow: auto;
  }
  .scheduler-col {
    display: flex;
    flex-direction: column;
    overflow: hidden;
    height: 100%;
  }
  /* original schedulers rows: auto 7.75rem minmax(7.75rem,13rem) minmax(7.75rem,1fr) */
  .running-section {
    height: 7.75rem;
    overflow-y: auto;
  }
  .pending-section {
    min-height: 7.75rem;
    max-height: 13rem;
    overflow-y: auto;
  }
  .waiting-section {
    min-height: 7.75rem;
    flex-grow: 1;
    overflow-y: auto;
  }
  .log-col {
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  .bar-title {
    font-size: 1.25rem;
    margin: auto 0.5rem auto;
  }
  .log-col .log-view {
    flex-grow: 1;
    margin: 0.3125rem;
    padding: 0.625rem;
    overflow-y: auto;
  }
</style>
