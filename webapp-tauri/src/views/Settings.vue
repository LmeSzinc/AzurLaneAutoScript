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
  if (name === 'Manage') {
    router.push('/devtools')
    return
  }
  // Home or an instance: both show the overview page
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
</script>

<template>
  <div class="settings">
    <AppAside :active="activeInstance" @select="onAsideSelect" />
    <AppMenu @overview="router.push('/')" @task="onMenuTask" />

    <div class="content">
      <h4 v-if="selectedTask">{{ t(`Task.${selectedTask}.name`) }}</h4>

      <!-- tool tasks: status + log view -->
      <div v-if="isToolTask" class="tool-view">
        <div class="card tool-status-card">
          <div class="card-header">
            {{ t(`Task.${selectedTask}.name`) }}
            <button
              class="btn btn-sm float-end"
              :class="toolAlive ? 'btn-danger' : 'btn-success'"
              @click="toggleTool"
            >
              {{ toolAlive ? t('Gui.Button.Stop') : t('Gui.Button.Start') }}
            </button>
          </div>
          <div class="card-body">
            <pre class="tool-log"><code>{{ (logs[activeInstance] ?? []).join('\n') }}</code></pre>
          </div>
        </div>
      </div>

      <template v-else>
        <p v-if="selectedTask && t(`Task.${selectedTask}.help`) !== `Task.${selectedTask}.help`" class="text-muted">
          {{ t(`Task.${selectedTask}.help`) }}
        </p>
        <div v-for="(groupArgs, groupKey) in schema[selectedTask] ?? {}" :key="groupKey" class="card group-card">
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
  background: #23292e;
  border-color: #39424a;
}
.group-card .card-header {
  background: #2a3137;
  color: #eaeaea;
  font-weight: 600;
}
.saving-hint {
  font-size: 12px;
  color: #4cd07d;
}
.tool-status-card {
  margin-top: 0.6rem;
}
.tool-log {
  margin: 0;
  max-height: 60vh;
  overflow-y: auto;
  background: #16191d;
  color: #d4d9de;
  padding: 8px;
  font-size: 12px;
  border-radius: 4px;
  white-space: pre-wrap;
}
</style>
