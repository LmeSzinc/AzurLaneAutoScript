<script lang="ts">
  import { api } from '../api/client'
  import { t, loadI18n } from '../api/i18n.svelte'
  import { logs, schedulers, status } from '../api/store.svelte'
  import { push } from '../router.svelte'
  import AppAside from '../components/AppAside.svelte'
  import AppMenu from '../components/AppMenu.svelte'
  import LogView from '../components/LogView.svelte'

  interface SchedulerTask {
    command: string
    next_run: string
  }

  const activeInstance = $derived(status.instances[0]?.name ?? 'alas')
  const instanceAlive = $derived(status.instances.find((i) => i.name === activeInstance)?.alive ?? false)
  /** Live snapshot pushed by the bot process via SSE; empty until the first event. */
  const scheduler = $derived(
    schedulers[activeInstance] ?? { current: null, pending: [] as SchedulerTask[], waiting: [] as SchedulerTask[] },
  )
  /** Queue column: pending tasks excluding the one currently running. */
  const pendingShown = $derived(scheduler.pending.filter((p) => p.command !== scheduler.current))
  /** The running task's scheduled time (looked up in pending or waiting). */
  const currentTask = $derived(
    scheduler.current
      ? (scheduler.pending.find((p) => p.command === scheduler.current) ??
          scheduler.waiting.find((p) => p.command === scheduler.current) ??
          null)
      : null,
  )
  let keepBottom = $state(true)
  const EMPTY_LOGS: string[] = []

  /** One-shot REST bootstrap: the backend's in-memory snapshot cache is
   *  cold on a fresh backend start (and absent while the bot never ran),
   *  so fetch once to fill the three columns; SSE takes over afterwards. */
  async function refreshScheduler() {
    if (!activeInstance) return
    const res = await api.scheduler(activeInstance)
    schedulers[activeInstance] = {
      current: res.running[0]?.command ?? null,
      pending: res.pending,
      waiting: res.waiting,
    }
  }

  async function toggleScheduler() {
    if (instanceAlive) {
      await api.stop(activeInstance)
    } else {
      await api.run(activeInstance)
    }
    // Status and scheduler updates arrive via SSE.
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

  // Auto-scroll is handled inside LogView.

  $effect(() => {
    void loadI18n()
    // Fills the columns at mount (and when the active instance changes);
    // no periodic polling - live updates come over the SSE stream.
    void refreshScheduler()
  })
</script>

<div class="home">
  <AppAside active={activeInstance} onselect={onAsideSelect} />
  <AppMenu onoverview={() => push('/')} ontask={(task) => goSettings(task)} />

  <div class="content overview">
    <!-- schedulers column -->
    <section class="scheduler-col">
      <div class="scheduler-bar">
        <span class="bar-title">{t('Gui.Overview.Scheduler')}</span>
        <button class="btn" class:btn-off={instanceAlive} class:btn-on={!instanceAlive} onclick={toggleScheduler}>
          {instanceAlive ? t('Gui.Button.Stop') : t('Gui.Button.Start')}
        </button>
      </div>

      <div class="running-section">
        <div class="running-section-title">{t('Gui.Overview.Running')}</div>
        <hr class="hr-group" />
        <div class="running-tasks">
          {#if !scheduler.current}
            <div class="overview-notask-text">{t('Gui.Overview.NoTask')}</div>
          {/if}
          {#if scheduler.current}
            <div class="overview-task">
              <div>
                <div class="arg-title">{t(`Task.${scheduler.current}.name`)}</div>
                <div class="arg-help">{currentTask?.next_run ?? ''}</div>
              </div>
              <button class="btn btn-off" onclick={() => goSettings(scheduler.current!)}>
                {t('Gui.Button.Setting')}
              </button>
            </div>
          {/if}
        </div>
      </div>

      <div class="pending-section">
        <div class="pending-section-title">{t('Gui.Overview.Pending')}</div>
        <hr class="hr-group" />
        <div class="pending-tasks">
          {#if pendingShown.length === 0}
            <div class="overview-notask-text">{t('Gui.Overview.NoTask')}</div>
          {/if}
          {#each pendingShown as task (task.command)}
            <div class="overview-task">
              <div>
                <div class="arg-title">{t(`Task.${task.command}.name`)}</div>
                <div class="arg-help">{task.next_run}</div>
              </div>
              <button class="btn btn-off" onclick={() => goSettings(task.command)}>
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
              <button class="btn btn-off" onclick={() => goSettings(task.command)}>
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
          <button
            class="btn"
            class:btn-on={keepBottom}
            class:btn-off={!keepBottom}
            onclick={() => (keepBottom = !keepBottom)}
          >
            {keepBottom ? t('Gui.Button.ScrollON') : t('Gui.Button.ScrollOFF')}
          </button>
        </div>
      </div>
      <LogView class="log-view" lines={logs[activeInstance] ?? EMPTY_LOGS} {keepBottom} />
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
    grid-template-rows: minmax(0, 1fr);
    gap: 0.625rem;
    overflow: hidden;
  }
  .scheduler-col {
    display: flex;
    flex-direction: column;
    overflow: hidden;
    height: 100%;
    min-height: 0;
  }
  /* original schedulers rows: auto 7.75rem minmax(7.75rem,13rem) minmax(7.75rem,1fr) */
  .running-section {
    height: 7.75rem;
    flex-shrink: 0;
    overflow-y: auto;
  }
  .pending-section {
    min-height: 7.75rem;
    max-height: 13rem;
    flex-shrink: 0;
    overflow-y: auto;
  }
  .waiting-section {
    min-height: 7.75rem;
    flex-grow: 1;
    flex-shrink: 1;
    overflow-y: auto;
  }
  .log-col {
    display: flex;
    flex-direction: column;
    overflow: hidden;
    min-height: 0;
  }
  .bar-title {
    font-size: 1.25rem;
    margin: auto 0.5rem auto;
  }
</style>
