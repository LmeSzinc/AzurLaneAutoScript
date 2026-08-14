<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api } from '@/api/client'
import { loadI18n, t } from '@/api/i18n'
import type { MenuSchema } from '@/api/types'

const emit = defineEmits<{
  overview: []
  task: [task: string]
}>()

const menu = ref<MenuSchema>({})
const activeTask = ref('')
/** Collapse groups are folded by default */
const collapsedGroups = ref<Record<string, boolean>>({})

function toggleGroup(name: string) {
  collapsedGroups.value[name] = !collapsedGroups.value[name]
}

function isGroupOpen(name: string): boolean {
  return collapsedGroups.value[name] === true
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
      class="btn-menu"
      :class="{ 'btn-menu-active': activeTask === '' }"
      @click="activeTask = ''; emit('overview')"
    >
      {{ t('Gui.MenuAlas.Overview') }}
    </button>

    <template v-for="group in groups" :key="group.name">
      <div v-if="group.collapse" class="menu-collapse">
        <button class="menu-collapse-title" @click="toggleGroup(group.name)">
          <span class="collapse-arrow" :class="{ 'collapse-arrow-open': isGroupOpen(group.name) }">▸</span>
          {{ t(`Menu.${group.name}.name`) }}
        </button>
        <div v-show="isGroupOpen(group.name)">
          <button
            v-for="task in group.tasks"
            :key="task"
            class="btn-menu"
            :class="{ 'btn-menu-active': activeTask === task }"
            @click="selectTask(task)"
          >
            {{ t(`Task.${task}.name`) }}
          </button>
        </div>
      </div>
      <template v-else>
        <div class="hr-task-group-box">
          <span class="hr-task-group-line" />
          <span class="hr-task-group-text">{{ t(`Menu.${group.name}.name`) }}</span>
          <span class="hr-task-group-line" />
        </div>
        <button
          v-for="task in group.tasks"
          :key="task"
          class="btn-menu btn-menu-indent"
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
  flex-shrink: 0;
  width: 12rem;
  padding-left: 0.5rem;
  padding-right: 0.5rem;
  padding-top: 1.2rem;
  overflow-y: auto;
  background: #20262b;
}
.btn-menu {
  display: block;
  width: 100%;
  font-weight: 400;
  font-size: 0.875rem;
  background-color: transparent;
  color: #cfd4d9;
  padding: 0.2rem 0.75rem;
  border-radius: 0;
  border: 0 solid;
  border-left: 3px solid transparent;
  white-space: pre-wrap;
  text-align: left;
  cursor: pointer;
}
.btn-menu:hover,
.btn-menu-active {
  font-weight: bold;
  border-left-color: #4c9aff;
  padding-right: 0.625rem;
  color: #eaeaea;
}
.btn-menu-indent {
  padding-left: 1.5rem;
}
.menu-collapse-title {
  display: block;
  width: 100%;
  font-size: 0.75rem;
  text-transform: uppercase;
  color: #8a939c;
  background: transparent;
  border: none;
  text-align: left;
  cursor: pointer;
  padding: 0.4rem 0.2rem 0.2rem;
  margin-top: 0.3rem;
}
.menu-collapse-title:hover {
  color: #cfd4d9;
}
.collapse-arrow {
  display: inline-block;
  transition: transform 0.15s ease;
  margin-right: 2px;
}
.collapse-arrow-open {
  transform: rotate(90deg);
}
.hr-task-group-box {
  display: flex;
  align-items: center;
  margin: 0.6rem 0.2rem 0.2rem;
}
.hr-task-group-line {
  flex: 1;
  border-top: 1px solid #39424a;
}
.hr-task-group-text {
  font-size: 0.75rem;
  color: #8a939c;
  margin: 0 0.5rem;
}
</style>
