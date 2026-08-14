<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/api/client'
import { loadI18n, t } from '@/api/i18n'
import { logs, refreshStatus, status } from '@/api/store'
import type { ArgDefinition } from '@/api/types'
import AppAside from '@/components/AppAside.vue'
import AppMenu from '@/components/AppMenu.vue'
import DynamicForm from '@/components/DynamicForm.vue'

const route = useRoute()
const router = useRouter()

const selectedTask = ref('')
const schema = ref<Record<string, Record<string, Record<string, ArgDefinition>>>>({})
const config = ref<Record<string, unknown>>({})
const activeInstance = computed(() => status.instances[0]?.name ?? 'alas')
const saving = ref(false)
/** Tasks whose page is 'tool' show a status view instead of the form */
const toolTasks = ref<Set<string>>(new Set())
const toolAlive = ref(false)
const toolKeepBottom = ref(true)
const toolLogEl = ref<HTMLElement | null>(null)

const isToolTask = computed(() => toolTasks.value.has(selectedTask.value))

async function loadTask(task: string) {
  selectedTask.value = task
  const { menu, args } = await api.schema('alas')
  for (const data of Object.values(menu)) {
    if (data.page === 'tool') {
      for (const name of data.tasks ?? []) {
        toolTasks.value.add(name)
      }
    }
  }
  schema.value = args
  config.value = await api.config(activeInstance.value)
}

async function refreshToolState() {
  if (isToolTask.value && activeInstance.value) {
    const sched = await api.scheduler(activeInstance.value)
    toolAlive.value = sched.alive
  }
}

async function toggleTool() {
  if (toolAlive.value) {
    await api.stop(activeInstance.value)
  } else {
    await api.run(activeInstance.value)
  }
  await refreshToolState()
}

async function saveValue(path: string, value: unknown) {
  saving.value = true
  try {
    await api.saveConfig(activeInstance.value, { [path]: value })
    config.value = await api.config(activeInstance.value)
  } finally {
    saving.value = false
  }
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
  router.replace({ path: '/settings', query: { task } })
}

onMounted(async () => {
  void loadI18n('zh-CN')
  await refreshStatus()
  const task = (route.query.task as string) || 'Alas'
  await loadTask(task)
  await refreshToolState()
})

watch(
  () => route.query.task,
  async (task) => {
    if (task && task !== selectedTask.value) {
      await loadTask(task as string)
      await refreshToolState()
    }
  },
)

// Auto-scroll the tool log view
watch(
  () => logs[activeInstance.value]?.length,
  () => {
    if (toolKeepBottom.value && toolLogEl.value) {
      toolLogEl.value.scrollTop = toolLogEl.value.scrollHeight
    }
  },
)
</script>

<template>
  <div class="settings">
    <AppAside :active="activeInstance" @select="onAsideSelect" />
    <AppMenu @overview="router.push('/')" @task="onMenuTask" />

    <div class="content">
      <h4 v-if="selectedTask">{{ t(`Task.${selectedTask}.name`) }}</h4>

      <!-- tool tasks: scheduler bar (top) + form + log (bottom) -->
      <div v-else-if="isToolTask" class="tool-view">
        <div class="tool-bar">
          <span class="col-title">{{ t('Gui.Overview.Scheduler') }}</span>
          <button
            class="btn btn-sm"
            :class="toolAlive ? 'btn-danger' : 'btn-success'"
            @click="toggleTool"
          >
            {{ toolAlive ? t('Gui.Button.Stop') : t('Gui.Button.Start') }}
          </button>
          <span class="col-title ms-auto">{{ t('Gui.Overview.Log') }}</span>
          <button class="btn btn-sm btn-outline-light" @click="toolKeepBottom = !toolKeepBottom">
            {{ toolKeepBottom ? t('Gui.Button.ScrollON') : t('Gui.Button.ScrollOFF') }}
          </button>
        </div>

        <div v-for="(groupArgs, groupKey) in schema[selectedTask] ?? {}" :key="groupKey" class="card group-card">
          <template v-if="groupKey !== 'Storage'">
            <div class="card-header">
              {{ t(`${groupKey}._info.name`) }}
            </div>
            <div class="card-body">
              <DynamicForm
                :args="groupArgs"
                :group="groupKey"
                :task="selectedTask"
                :config="config"
                @save="saveValue"
              />
            </div>
          </template>
        </div>

        <pre ref="toolLogEl" class="tool-log"><code>{{ (logs[activeInstance] ?? []).join('\n') }}</code></pre>
      </div>

      <template v-else>
        <p v-if="selectedTask && t(`Task.${selectedTask}.help`) !== `Task.${selectedTask}.help`" class="text-muted">
          {{ t(`Task.${selectedTask}.help`) }}
        </p>
        <div v-for="(groupArgs, groupKey) in schema[selectedTask] ?? {}" :key="groupKey" class="card group-card">
          <template v-if="groupKey !== 'Storage'">
            <div class="card-header">
              {{ t(`${groupKey}._info.name`) }}
            </div>
            <div class="card-body">
              <DynamicForm
                :args="groupArgs"
                :group="groupKey"
                :task="selectedTask"
                :config="config"
                @save="saveValue"
              />
            </div>
          </template>
        </div>
        <span v-if="saving" class="saving-hint">saving...</span>
      </template>
    </div>
  </div>
</template>

<style scoped>
.settings {
  height: 100%;
  display: flex;
  overflow: hidden;
}
.content {
  flex-grow: 1;
  padding: 1rem;
  overflow-y: auto;
}
.group-card {
  margin-bottom: 14px;
}
.group-card .card-header {
  font-weight: 600;
}
.saving-hint {
  font-size: 12px;
  color: #4cd07d;
}
.tool-status-card {
  margin-top: 0.6rem;
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
  color: #d4d9de;
  padding: 8px;
  font-size: 12px;
  border-radius: 4px;
  white-space: pre-wrap;
}
</style>
