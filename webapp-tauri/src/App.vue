<script setup lang="ts">
import { watch } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import { status } from '@/api/store'

const THEMES = ['default', 'dark', 'light', 'minty', 'yeti', 'sketchy']
let themeLink: HTMLLinkElement | null = null
let alasLink: HTMLLinkElement | null = null

function applyTheme(theme: string) {
  const name = THEMES.includes(theme) ? theme : 'default'
  const bsTheme = name === 'light' ? 'default' : name
  const alasTheme = name === 'dark' ? 'dark-alas' : name === 'light' ? 'light-alas' : 'alas'
  if (themeLink) {
    themeLink.remove()
  }
  if (alasLink) {
    alasLink.remove()
  }
  themeLink = document.createElement('link')
  themeLink.rel = 'stylesheet'
  themeLink.href = `css/${bsTheme}.min.css`
  document.head.appendChild(themeLink)
  alasLink = document.createElement('link')
  alasLink.rel = 'stylesheet'
  alasLink.href = `css/${alasTheme}.css`
  document.head.appendChild(alasLink)
}

applyTheme(status.theme)
watch(
  () => status.theme,
  (theme) => applyTheme(theme),
)
</script>

<template>
  <div id="app">
    <AppHeader />
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<style>
html,
body,
#app {
  margin: 0;
  padding: 0;
  height: 100vh;
  overflow: hidden;
  background: #1d2226;
  color: #eaeaea;
  font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
}
.app-main {
  height: calc(100vh - 32px);
}
/* Mobile: collapse panels to full width below 768px */
@media (max-width: 767px) {
  .app-main {
    height: calc(100vh - 32px);
  }
}
</style>
