<script setup lang="ts">
import { computed } from 'vue'
import { invoke } from '@tauri-apps/api/core'
import { useRoute } from 'vue-router'
import { status } from '@/api/store'
import { t } from '@/api/i18n'

const route = useRoute()
const isTauri = '__TAURI_INTERNALS__' in window

const stateText = computed(() => {
  const state = status.instances[0]?.state ?? 0
  if (state === 1) return t('Gui.Status.Running')
  if (state === 3) return t('Gui.Status.Warning')
  if (state === 4) return t('Gui.Status.Updating')
  return t('Gui.Status.Inactive')
})

const stateClass = computed(() => {
  const state = status.instances[0]?.state ?? 0
  if (state === 1) return 'header-state-running'
  if (state === 3) return 'header-state-warning'
  if (state === 4) return 'header-state-updating'
  return 'header-state-inactive'
})

const pageTitle = computed(() => {
  if (route.path === '/settings') {
    const task = (route.query.task as string) || ''
    return task ? t(`Task.${task}.name`) : ''
  }
  if (route.path === '/develop') return t('Gui.Aside.Home')
  if (route.path === '/manage') return t('Gui.AppManage.PageTitle')
  return t('Gui.MenuAlas.Overview')
})

function min() {
  void invoke('window_min')
}
function max() {
  void invoke('window_max')
}
function close() {
  void invoke('window_close')
}
</script>

<template>
  <header class="app-header">
    <img class="header-icon" src="@/assets/icon/alas.svg" alt="Alas" />
    <span class="header-text">Alas</span>
    <span class="header-state" :class="stateClass">
      <span class="header-state-dot" />
      {{ stateText }}
    </span>
    <div class="header-title">
      <span class="header-title-text">{{ pageTitle }}</span>
    </div>
    <div v-if="isTauri" class="app-header-controls">
      <button class="header-btn" title="Minimize" @click="min">&#x2212;</button>
      <button class="header-btn" title="Maximize" @click="max">&#x25A1;</button>
      <button class="header-btn header-btn-close" title="Close" @click="close">&#x2715;</button>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  display: grid;
  grid-auto-flow: column;
  grid-template-columns: 4.4rem 4rem auto 1fr auto;
  align-items: center;
  height: 2.5rem;
  user-select: none;
  -webkit-app-region: drag;
}
.header-icon {
  width: 42px;
  height: 42px;
  margin: 0.25rem auto;
  border-radius: 1.5rem;
}
.header-text {
  font-size: 1.5rem;
  font-weight: bold;
  margin: auto !important;
}
.header-state {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.85rem;
  margin: auto;
}
.header-state-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #8a939c;
}
.header-state-running .header-state-dot {
  background: #4cd07d;
}
.header-state-warning .header-state-dot {
  background: #e6a23c;
}
.header-state-updating .header-state-dot {
  background: #4c9aff;
}
.header-title {
  margin: auto;
}
.header-title-text {
  font-size: 1.2rem;
  margin: auto;
  overflow: hidden;
  text-align: center;
  white-space: nowrap;
}
.app-header-controls {
  display: flex;
  height: 100%;
  -webkit-app-region: no-drag;
}
.header-btn {
  width: 44px;
  height: 100%;
  border: none;
  background: transparent;
  font-size: 12px;
  cursor: pointer;
}
.header-btn:hover {
  background: rgba(255, 255, 255, 0.08);
}
.header-btn-close:hover {
  background: #c42b1c;
  color: #fff;
}
</style>
