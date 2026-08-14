<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api/client'
import { loadI18n, t } from '@/api/i18n'
import { connected, logs, refreshStatus, status } from '@/api/store'
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
  if (name === 'Manage') {
    router.push('/devtools')
    return
  }
  // Home or an instance: both show the overview page
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
  void loadI18n('zh-CN')
  await refreshStatus()
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

    <div class="content">
      <!-- schedulers column -->
      <section class="scheduler-col">
        <div class="scheduler-bar">
          <span class="col-title">{{ t('Gui.Overview.Scheduler') }}</span>
          <button
            class="btn btn-sm"
            :class="scheduler.alive ? 'btn-danger' : 'btn-success'"
            @click="toggleScheduler"
          >
            {{ scheduler.alive ? t('Gui.Button.Stop') : t('Gui.Button.Start') }}
          </button>
        </div>

        <div v-for="(section, key) in [
          { title: t('Gui.Overview.Running'), tasks: scheduler.running },
          { title: t('Gui.Overview.Pending'), tasks: scheduler.pending },
          { title: t('Gui.Overview.Waiting'), tasks: scheduler.waiting },
        ]" :key="key" class="task-section">
          <div class="task-section-title">{{ section.title }}</div>
          <hr class="hr-group" />
          <div v-if="section.tasks.length === 0" class="notask-text">
            {{ t('Gui.Overview.NoTask') }}
          </div>
          <div v-for="task in section.tasks" :key="task.command" class="task-row">
            <div class="task-info">
              <div class="task-title">{{ t(`Task.${task.command}.name`) }}</div>
              <div class="task-help">{{ task.next_run }}</div>
            </div>
            <button class="btn btn-sm btn-outline-light" @click="goSettings(task.command)">
              {{ t('Gui.Button.Setting') }}
            </button>
          </div>
        </div>
      </section>

      <!-- logs column -->
      <section class="log-col">
        <div class="log-bar">
          <span class="col-title">{{ t('Gui.Overview.Log') }}</span>
          <button class="btn btn-sm btn-outline-light" @click="keepBottom = !keepBottom">
            {{ keepBottom ? t('Gui.Button.ScrollON') : t('Gui.Button.ScrollOFF') }}
          </button>
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
  display: grid;
  grid-template-columns: minmax(240px, 2fr) minmax(280px, 3fr);
  gap: 0.4rem;
  padding: 0.625rem;
  overflow: hidden;
}
.scheduler-col,
.log-col {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.scheduler-bar,
.log-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 500;
  margin: 0.3125rem;
  padding: 0.625rem;
}
.col-title {
  font-size: 1.25rem;
  margin: auto 0.5rem auto;
}
.task-section {
  font-weight: 500;
  margin: 0.3125rem;
  padding: 0.625rem;
  overflow-y: auto;
}
.task-section-title {
  font-weight: 600;
}
.hr-group {
  margin-top: 0.25rem;
  margin-bottom: 0.25rem;
  border-color: #39424a;
}
.notask-text {
  text-align: center;
  font-size: 0.875rem;
  color: darkgrey;
  padding: 0.6rem 0;
}
.task-row {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: 0.5rem;
  margin: 0.125rem 0.625rem 0.125rem 0.375rem;
  padding: 0.3rem 0.4rem;
  border-radius: 4px;
}
.task-row:hover {
  background: rgba(255, 255, 255, 0.04);
}
.task-title {
  font-size: 1rem;
  font-weight: 500;
  margin: 0 0.25rem;
  overflow-wrap: break-word;
  color: #eaeaea;
}
.task-help {
  font-size: 0.8rem;
  margin: 0.2rem 0.25rem 0.1rem;
  overflow-wrap: break-word;
  color: #8a939c;
}
.log-view {
  flex-grow: 1;
  margin: 0.3125rem;
  padding: 0.625rem;
  overflow-y: auto;
  background: #16191d;
  color: #d4d9de;
  font-size: 12px;
  border-radius: 4px;
  white-space: pre-wrap;
}
.conn {
  font-size: 12px;
}
.conn-on {
  color: #4cd07d;
}
.conn-off {
  color: #e0645c;
}
</style>
