<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api/client'
import { loadI18n, t } from '@/api/i18n'
import { logs, refreshStatus, status } from '@/api/store'
import AppAside from '@/components/AppAside.vue'
import AppMenu from '@/components/AppMenu.vue'

const router = useRouter()

interface SchedulerTask {
  command: string
  next_run: string
}

const scheduler = ref<{ alive: boolean; running: SchedulerTask[]; pending: SchedulerTask[]; waiting: SchedulerTask[] }>({
  alive: false,
  running: [],
  pending: [],
  waiting: [],
})

const activeInstance = computed(() => status.instances[0]?.name ?? 'alas')
const keepBottom = ref(true)
const logEl = ref<HTMLElement | null>(null)

async function refreshScheduler() {
  if (!activeInstance.value) return
  scheduler.value = await api.scheduler(activeInstance.value)
}

async function toggleScheduler() {
  if (scheduler.value.alive) {
    await api.stop(activeInstance.value)
  } else {
    await api.run(activeInstance.value)
  }
  await refreshStatus()
  await refreshScheduler()
}

function goSettings(task: string) {
  router.push({ path: '/settings', query: { task } })
}

function onAsideSelect(name: string) {
  if (name === 'Home') {
    router.push('/develop')
    return
  }
  if (name === 'Manage') {
    router.push('/manage')
    return
  }
  // instance: stay on the overview page
  router.push('/')
}

function onMenuTask(task: string) {
  goSettings(task)
}

// Auto-scroll the log view when keepBottom is on
function scrollLog() {
  if (keepBottom.value && logEl.value) {
    logEl.value.scrollTop = logEl.value.scrollHeight
  }
}

let timer: number | undefined

onMounted(async () => {
  await refreshStatus()
  void loadI18n()
  await refreshScheduler()
  timer = window.setInterval(() => {
    void refreshStatus()
    void refreshScheduler()
    scrollLog()
  }, 5000)
})

// Scroll as soon as new logs arrive over the websocket
watch(
  () => logs[activeInstance.value]?.length,
  () => scrollLog(),
)

onUnmounted(() => {
  window.clearInterval(timer)
})
</script>

<template>
  <div class="home">
    <AppAside :active="activeInstance" @select="onAsideSelect" />
    <AppMenu @overview="router.push('/')" @task="onMenuTask" />

    <div class="content overview">
      <!-- schedulers column -->
      <section class="scheduler-col">
        <div class="scheduler-bar">
          <span class="bar-title">{{ t('Gui.Overview.Scheduler') }}</span>
          <button
            class="btn btn-sm"
            :class="scheduler.alive ? 'btn-danger' : 'btn-success'"
            @click="toggleScheduler"
          >
            {{ scheduler.alive ? t('Gui.Button.Stop') : t('Gui.Button.Start') }}
          </button>
        </div>

        <div class="running-section">
          <div class="running-section-title">{{ t('Gui.Overview.Running') }}</div>
          <hr class="hr-group" />
          <div class="running-tasks">
            <div v-if="scheduler.running.length === 0" class="overview-notask-text">
              {{ t('Gui.Overview.NoTask') }}
            </div>
            <div v-for="task in scheduler.running" :key="task.command" class="overview-task">
              <div>
                <div class="arg-title">{{ t(`Task.${task.command}.name`) }}</div>
                <div class="arg-help">{{ task.next_run }}</div>
              </div>
              <button class="btn btn-sm btn-adaptive" @click="goSettings(task.command)">
                {{ t('Gui.Button.Setting') }}
              </button>
            </div>
          </div>
        </div>

        <div class="pending-section">
          <div class="pending-section-title">{{ t('Gui.Overview.Pending') }}</div>
          <hr class="hr-group" />
          <div class="pending-tasks">
            <div v-if="scheduler.pending.length === 0" class="overview-notask-text">
              {{ t('Gui.Overview.NoTask') }}
            </div>
            <div v-for="task in scheduler.pending" :key="task.command" class="overview-task">
              <div>
                <div class="arg-title">{{ t(`Task.${task.command}.name`) }}</div>
                <div class="arg-help">{{ task.next_run }}</div>
              </div>
              <button class="btn btn-sm btn-adaptive" @click="goSettings(task.command)">
                {{ t('Gui.Button.Setting') }}
              </button>
            </div>
          </div>
        </div>

        <div class="waiting-section">
          <div class="waiting-section-title">{{ t('Gui.Overview.Waiting') }}</div>
          <hr class="hr-group" />
          <div class="waiting-tasks">
            <div v-if="scheduler.waiting.length === 0" class="overview-notask-text">
              {{ t('Gui.Overview.NoTask') }}
            </div>
            <div v-for="task in scheduler.waiting" :key="task.command" class="overview-task">
              <div>
                <div class="arg-title">{{ t(`Task.${task.command}.name`) }}</div>
                <div class="arg-help">{{ task.next_run }}</div>
              </div>
              <button class="btn btn-sm btn-adaptive" @click="goSettings(task.command)">
                {{ t('Gui.Button.Setting') }}
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- logs column -->
      <section class="log-col">
        <div class="log-bar">
          <span class="bar-title">{{ t('Gui.Overview.Log') }}</span>
          <div class="log-bar-btns">
            <button class="btn btn-sm btn-adaptive" @click="keepBottom = !keepBottom">
              {{ keepBottom ? t('Gui.Button.ScrollON') : t('Gui.Button.ScrollOFF') }}
            </button>
          </div>
        </div>
        <pre ref="logEl" class="log-view"><code>{{ (logs[activeInstance] ?? []).join('\n') }}</code></pre>
      </section>
    </div>
  </div>
</template>

<style scoped>
.home {
  height: 100%;
  display: flex;
  overflow: hidden;
}
.content {
  flex-grow: 1;
  padding: 0.625rem;
  grid-template-columns: minmax(240px, 2fr) minmax(280px, 3fr);
  gap: 0.4rem;
  overflow: auto;
}
.scheduler-col,
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
