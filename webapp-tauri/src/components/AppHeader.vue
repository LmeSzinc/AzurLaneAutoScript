<script setup lang="ts">
import { invoke } from '@tauri-apps/api/core'

const isTauri = '__TAURI_INTERNALS__' in window

function min() {
  void invoke('window_min')
}
function max() {
  void invoke('window_max')
}
function close() {
  void invoke('window_close')
}

function dragRegion(event: MouseEvent) {
  if (!isTauri) return
  // Double click toggles maximize, matching the previous Electron behavior
  if (event.detail === 2) {
    max()
  }
}
</script>

<template>
  <header class="app-header" data-tauri-drag-region @dblclick="dragRegion">
    <div class="app-header-left" data-tauri-drag-region>
      <img class="header-icon" src="@/assets/icon/alas.svg" alt="Alas" data-tauri-drag-region />
      <span class="header-text" data-tauri-drag-region>Alas</span>
      <span class="header-title-text" data-tauri-drag-region></span>
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
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 2.5rem;
  user-select: none;
  -webkit-app-region: drag;
}
.app-header-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding-left: 10px;
}
.header-icon {
  width: 42px;
  height: 42px;
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
