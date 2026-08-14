<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api } from '@/api/client'
import { loadI18n, t } from '@/api/i18n'
import { collapsedGroups } from '@/api/store'
import type { MenuSchema } from '@/api/types'

const emit = defineEmits<{
  overview: []
  task: [task: string]
}>()

const menu = ref<MenuSchema>({})
const activeTask = ref('')

function toggleGroup(name: string) {
  collapsedGroups[name] = !collapsedGroups[name]
}

function isGroupOpen(name: string): boolean {
  return collapsedGroups[name] === true
}

const groups = computed(() => {
  const result: { name: string; collapse: boolean; tasks: string[] }[] = []
  for (const [name, data] of Object.entries(menu.value)) {
    result.push({
      name,
      collapse: data.menu === 'collapse',
      tasks: data.tasks ?? [],
    })
  }
  return result
})

function selectTask(task: string) {
  activeTask.value = task
  emit('task', task)
}

onMounted(async () => {
  const schema = await api.schema('alas')
  menu.value = schema.menu
  void loadI18n()
})
</script>

<template>
  <nav class="app-menu">
    <button
      class="btn btn-menu"
      :class="{ 'btn-menu-active': activeTask === '' }"
      @click="activeTask = ''; emit('overview')"
    >
      {{ t('Gui.MenuAlas.Overview') }}
    </button>

    <template v-for="group in groups" :key="group.name">
      <details v-if="group.collapse" class="menu-collapse" :open="isGroupOpen(group.name)" @toggle="toggleGroup(group.name)">
        <summary>{{ t(`Menu.${group.name}.name`) }}</summary>
        <div>
          <button
            v-for="task in group.tasks"
            :key="task"
            class="btn btn-menu"
            :class="{ 'btn-menu-active': activeTask === task }"
            @click="selectTask(task)"
          >
            {{ t(`Task.${task}.name`) }}
          </button>
        </div>
      </details>
      <template v-else>
        <div class="hr-task-group-box">
          <span class="hr-task-group-line" />
          <span class="hr-task-group-text">{{ t(`Menu.${group.name}.name`) }}</span>
          <span class="hr-task-group-line" />
        </div>
        <button
          v-for="task in group.tasks"
          :key="task"
          class="btn btn-menu"
          :class="{ 'btn-menu-active': activeTask === task }"
          @click="selectTask(task)"
        >
          {{ t(`Task.${task}.name`) }}
        </button>
      </template>
    </template>
  </nav>
</template>

<style scoped>
.app-menu {
  z-index: 90;
  padding-left: 0.5rem;
  padding-right: 0.5rem;
  padding-top: 1.2rem;
  overflow-y: auto;
  width: 12rem;
  flex-shrink: 0;
}
.app-menu .btn-menu {
  display: block;
  width: 100%;
}
</style>
