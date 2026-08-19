<script lang="ts">
import { api } from "../api/client";
import { loadI18n, t } from "../api/i18n.svelte";
import { logs, schedulers, status } from "../api/store.svelte";
import AppAside from "../components/AppAside.svelte";
import AppMenu from "../components/AppMenu.svelte";
import LogView from "../components/LogView.svelte";
import { push } from "../router.svelte";

interface SchedulerTask {
  command: string;
  next_run: string;
}

const activeInstance = $derived(status.instances[0]?.name ?? "alas");
const instanceAlive = $derived(status.instances.find((i) => i.name === activeInstance)?.alive ?? false);
/** Live snapshot pushed by the bot process via SSE; empty until the first event. */
const scheduler = $derived(
  schedulers[activeInstance] ?? { current: null, pending: [] as SchedulerTask[], waiting: [] as SchedulerTask[] },
);
/** Queue column: pending tasks excluding the one currently running. */
const pendingShown = $derived(scheduler.pending.filter((p) => p.command !== scheduler.current));
/** The running task's scheduled time (looked up in pending or waiting). */
const currentTask = $derived(
  scheduler.current
    ? (scheduler.pending.find((p) => p.command === scheduler.current) ??
        scheduler.waiting.find((p) => p.command === scheduler.current) ??
        null)
    : null,
);
let keepBottom = $state(true);
const EMPTY_LOGS: string[] = [];

/** One-shot REST bootstrap: the backend's in-memory snapshot cache is
 *  cold on a fresh backend start (and absent while the bot never ran),
 *  so fetch once to fill the three columns; SSE takes over afterwards. */
async function refreshScheduler() {
  if (!activeInstance) return;
  const res = await api.scheduler(activeInstance);
  schedulers[activeInstance] = {
    current: res.running[0]?.command ?? null,
    pending: res.pending,
    waiting: res.waiting,
  };
}

async function toggleScheduler() {
  if (instanceAlive) {
    await api.stop(activeInstance);
  } else {
    await api.run(activeInstance);
  }
  // Status and scheduler updates arrive via SSE.
}

function goSettings(task: string) {
  push("/settings", { task });
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
  // instance: stay on the overview page
  push("/");
}

// Auto-scroll is handled inside LogView.

$effect(() => {
  void loadI18n();
  // Fills the columns at mount (and when the active instance changes);
  // no periodic polling - live updates come over the SSE stream.
  void refreshScheduler();
});
</script>

<div class="flex h-full overflow-hidden bg-surface-app">
  <AppAside active={activeInstance} onselect={onAsideSelect} />
  <AppMenu onoverview={() => push('/')} ontask={(task) => goSettings(task)} />

  <div
    class="grid min-w-0 grow gap-2.5 overflow-hidden bg-surface-app p-2.5 [grid-template-columns:minmax(16rem,20rem)_minmax(24rem,1fr)] [grid-template-rows:minmax(0,1fr)]"
  >
    <!-- schedulers column -->
    <section class="flex h-full min-h-0 flex-col overflow-hidden">
      <div class="panel m-1.25 flex items-center justify-between p-2.5 font-medium">
        <span class="mx-2 my-auto text-[1.25rem]">{t('Gui.Overview.Scheduler')}</span>
        <button
          class="btn m-0 rounded-none border-toggle"
          class:bg-accent={!instanceAlive}
          class:bg-surface-app={instanceAlive}
          class:text-white={!instanceAlive}
          class:text-body={instanceAlive}
          onclick={toggleScheduler}
        >
          {instanceAlive ? t('Gui.Button.Stop') : t('Gui.Button.Start')}
        </button>
      </div>

      <div class="panel m-1.25 grid h-[var(--space-section)] flex-shrink-0 overflow-y-auto p-2.5 font-medium [grid-auto-flow:row] [grid-template-rows:auto_auto_1fr]">
        <div class="mx-2.5 text-[1.25rem] font-medium">{t('Gui.Overview.Running')}</div>
        <hr class="my-1 border-0 bg-surface-hr [border-top:var(--hr-line)]" />
        <div class="h-full overflow-y-auto">
          {#if !scheduler.current}
            <div class="text-center text-[0.875rem] [color:darkgrey]">{t('Gui.Overview.NoTask')}</div>
          {/if}
          {#if scheduler.current}
            <div class="my-0.5 ml-1.5 mr-2.5 grid [grid-template-columns:1fr_auto]">
              <div>
                <div class="mx-1 text-base font-medium [overflow-wrap:break-word]">
                  {t(`Task.${scheduler.current}.name`)}
                </div>
                <div class="mx-1 mt-[0.2rem] mb-[0.1rem] text-[0.8rem] text-muted [overflow-wrap:break-word]">
                  {currentTask?.next_run ?? ''}
                </div>
              </div>
              <button class="btn m-0 rounded-none border-toggle bg-surface-app text-body" onclick={() => goSettings(scheduler.current!)}>
                {t('Gui.Button.Setting')}
              </button>
            </div>
          {/if}
        </div>
      </div>

      <div class="panel m-1.25 grid min-h-[var(--space-section)] max-h-52 flex-shrink-0 overflow-y-auto p-2.5 font-medium [grid-auto-flow:row] [grid-template-rows:auto_auto_1fr]">
        <div class="mx-2.5 text-[1.25rem] font-medium">{t('Gui.Overview.Pending')}</div>
        <hr class="my-1 border-0 bg-surface-hr [border-top:var(--hr-line)]" />
        <div class="h-full overflow-y-auto">
          {#if pendingShown.length === 0}
            <div class="text-center text-[0.875rem] [color:darkgrey]">{t('Gui.Overview.NoTask')}</div>
          {/if}
          {#each pendingShown as task (task.command)}
            <div class="my-0.5 ml-1.5 mr-2.5 grid [grid-template-columns:1fr_auto]">
              <div>
                <div class="mx-1 text-base font-medium [overflow-wrap:break-word]">
                  {t(`Task.${task.command}.name`)}
                </div>
                <div class="mx-1 mt-[0.2rem] mb-[0.1rem] text-[0.8rem] text-muted [overflow-wrap:break-word]">
                  {task.next_run}
                </div>
              </div>
              <button class="btn m-0 rounded-none border-toggle bg-surface-app text-body" onclick={() => goSettings(task.command)}>
                {t('Gui.Button.Setting')}
              </button>
            </div>
          {/each}
        </div>
      </div>

      <div class="panel m-1.25 grid min-h-[var(--space-section)] grow flex-shrink overflow-y-auto p-2.5 font-medium [grid-auto-flow:row] [grid-template-rows:auto_auto_1fr]">
        <div class="mx-2.5 text-[1.25rem] font-medium">{t('Gui.Overview.Waiting')}</div>
        <hr class="my-1 border-0 bg-surface-hr [border-top:var(--hr-line)]" />
        <div class="h-full overflow-y-auto">
          {#if scheduler.waiting.length === 0}
            <div class="text-center text-[0.875rem] [color:darkgrey]">{t('Gui.Overview.NoTask')}</div>
          {/if}
          {#each scheduler.waiting as task (task.command)}
            <div class="my-0.5 ml-1.5 mr-2.5 grid [grid-template-columns:1fr_auto]">
              <div>
                <div class="mx-1 text-base font-medium [overflow-wrap:break-word]">
                  {t(`Task.${task.command}.name`)}
                </div>
                <div class="mx-1 mt-[0.2rem] mb-[0.1rem] text-[0.8rem] text-muted [overflow-wrap:break-word]">
                  {task.next_run}
                </div>
              </div>
              <button class="btn m-0 rounded-none border-toggle bg-surface-app text-body" onclick={() => goSettings(task.command)}>
                {t('Gui.Button.Setting')}
              </button>
            </div>
          {/each}
        </div>
      </div>
    </section>

    <!-- logs column -->
    <section class="flex min-h-0 flex-col overflow-hidden">
      <div class="panel m-1.25 flex items-center justify-between p-2.5 font-medium">
        <span class="mx-2 my-auto text-[1.25rem]">{t('Gui.Overview.Log')}</span>
        <div class="grid [grid-auto-flow:column]">
          <button
            class="btn m-0 rounded-none border-toggle"
            class:bg-accent={keepBottom}
            class:bg-surface-app={!keepBottom}
            class:text-white={keepBottom}
            class:text-body={!keepBottom}
            onclick={() => (keepBottom = !keepBottom)}
          >
            {keepBottom ? t('Gui.Button.ScrollON') : t('Gui.Button.ScrollOFF')}
          </button>
        </div>
      </div>
      <LogView
        class="panel m-1.25 min-h-0 grow overflow-y-auto p-2.5 text-[0.85rem] leading-[1.2] whitespace-pre [color:inherit] [font-family:var(--font-mono)]"
        lines={logs[activeInstance] ?? EMPTY_LOGS}
        {keepBottom}
      />
    </section>
  </div>
</div>
