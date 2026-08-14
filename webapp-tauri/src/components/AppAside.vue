<script setup lang="ts">
import { api } from '@/api/client'
import { status } from '@/api/store'

const props = defineProps<{
  active?: string
}>()

const emit = defineEmits<{
  select: [name: string]
}>()

const LANGUAGES = ['zh-CN', 'en-US', 'ja-JP', 'zh-TW']
const THEMES = ['default', 'dark', 'light', 'minty', 'yeti', 'sketchy']

async function setLanguage(event: Event) {
  await api.setLanguage((event.target as HTMLSelectElement).value)
  window.location.reload()
}

async function setTheme(event: Event) {
  const theme = (event.target as HTMLSelectElement).value
  await api.setTheme(theme)
  status.theme = theme
}

function stateClass(state: number): string {
  if (state === 1) return 'aside-state-running'
  if (state === 3) return 'aside-state-warning'
  if (state === 4) return 'aside-state-updating'
  return ''
}
</script>

<template>
  <aside class="app-aside">
    <button
      class="btn-aside"
      :class="{ 'btn-aside-active': active === 'Home' }"
      @click="emit('select', 'Home')"
    >
      Home
    </button>
    <button
      v-for="inst in status.instances"
      :key="inst.name"
      class="btn-aside"
      :class="{ 'btn-aside-active': active === inst.name }"
      @click="emit('select', inst.name)"
    >
      <span class="aside-state-dot" :class="stateClass(inst.state)" />
      {{ inst.name }}
    </button>
    <button
      class="btn-aside"
      :class="{ 'btn-aside-active': active === 'Manage' }"
      @click="emit('select', 'Manage')"
    >
      Manage
    </button>

    <div class="aside-bottom">
      <select class="form-control form-control-sm mb-1" :value="status.language" @change="setLanguage">
        <option v-for="lang in LANGUAGES" :key="lang" :value="lang">{{ lang }}</option>
      </select>
      <select class="form-control form-control-sm" :value="status.theme" @change="setTheme">
        <option v-for="theme in THEMES" :key="theme" :value="theme">{{ theme }}</option>
      </select>
    </div>
  </aside>
</template>

<style scoped>
.app-aside {
  flex-shrink: 0;
  width: 4.5rem;
  padding-top: 1rem;
  padding-left: 0.125rem;
  padding-right: 0.325rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.btn-aside {
  width: 4rem;
  font-weight: 400;
  font-size: 0.8rem;
  background-color: transparent;
  padding: 8px 0 8px 7px;
  border-radius: 0;
  border: 0 solid;
  border-left: 4px solid transparent;
  text-align: left;
  cursor: pointer;
  margin-bottom: 0.2rem;
  overflow-wrap: break-word;
}
.btn-aside:hover,
.btn-aside-active {
  border-left-color: #4c9aff;
  padding-left: 3px;
  font-weight: bold;
}
.aside-state-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 3px;
  background: #8a939c;
}
.aside-state-running {
  background: #4cd07d;
}
.aside-state-warning {
  background: #e6a23c;
}
.aside-state-updating {
  background: #4c9aff;
}
.aside-bottom {
  margin-top: auto;
  padding: 0.5rem 0.2rem 0.8rem;
}
</style>
