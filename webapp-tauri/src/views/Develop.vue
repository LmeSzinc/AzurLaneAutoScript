<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api/client'
import { loadI18n, t } from '@/api/i18n'
import { refreshStatus, status } from '@/api/store'
import AppAside from '@/components/AppAside.vue'
const router = useRouter()

type SubPage = 'HomePage' | 'Update' | 'Remote' | 'Utils'
const page = ref<SubPage>('HomePage')

const LANGS = [
  { label: '简体中文', value: 'zh-CN' },
  { label: '繁體中文', value: 'zh-TW' },
  { label: 'English', value: 'en-US' },
  { label: '日本語', value: 'ja-JP' },
]
const THEMES = [
  { label: 'Light', value: 'default' },
  { label: 'Dark', value: 'dark' },
]

// updater data
const updateState = ref('idle')
const history = ref<{ local: string[] | null; upstream: string[] | null; history: string[][] }>({
  local: null,
  upstream: null,
  history: [],
})

async function refreshUpdate() {
  const [st, hist] = await Promise.all([api.updateStatus(), api.updateHistory()])
  updateState.value = st.state
  history.value = hist
}

async function checkUpdate() {
  await api.updateCheck()
  const timer = window.setInterval(async () => {
    const st = await api.updateStatus()
    updateState.value = st.state
    if (st.state !== 'checking') {
      window.clearInterval(timer)
      await refreshUpdate()
    }
  }, 1500)
}

async function runUpdate() {
  await api.updateRun()
  const timer = window.setInterval(async () => {
    const st = await api.updateStatus()
    updateState.value = st.state
    if (st.state !== 'updating') {
      window.clearInterval(timer)
      await refreshUpdate()
    }
  }, 2000)
}

async function setLanguage(lang: string) {
  await api.setLanguage(lang)
  status.language = lang
  // t() is reactive: once the new dictionary is loaded the UI re-renders.
  await loadI18n()
}

async function setTheme(theme: string) {
  await api.setTheme(theme)
  status.theme = theme
}

function onAsideSelect(name: string) {
  if (name === 'Manage') {
    router.push('/manage')
    return
  }
  // Home or an instance
  if (name === 'Home') {
    page.value = 'HomePage'
    return
  }
  router.push('/')
}

onMounted(async () => {
  void loadI18n()
  await refreshStatus()
  void refreshUpdate()
})
</script>

<template>
  <div class="develop-wrap">
    <AppAside active="Home" @select="onAsideSelect" />
    <nav class="dev-menu">
      <button
        class="btn-menu"
        :class="{ 'btn-menu-active': page === 'HomePage' }"
        @click="page = 'HomePage'"
      >
        {{ t('Gui.MenuDevelop.HomePage') }}
      </button>
      <button
        class="btn-menu"
        :class="{ 'btn-menu-active': page === 'Update' }"
        @click="page = 'Update'"
      >
        {{ t('Gui.MenuDevelop.Update') }}
      </button>
      <button
        class="btn-menu"
        :class="{ 'btn-menu-active': page === 'Remote' }"
        @click="page = 'Remote'"
      >
        {{ t('Gui.MenuDevelop.Remote') }}
      </button>
      <button
        class="btn-menu"
        :class="{ 'btn-menu-active': page === 'Utils' }"
        @click="page = 'Utils'"
      >
        {{ t('Gui.MenuDevelop.Utils') }}
      </button>
    </nav>

    <div class="content">
      <!-- HomePage -->
      <template v-if="page === 'HomePage'">
        <p class="center-text">Select your language / 选择语言</p>
        <div class="center-btns">
          <button
            v-for="lang in LANGS"
            :key="lang.value"
            class="btn btn-sm"
            :class="status.language === lang.value ? 'btn-primary' : 'btn-adaptive'"
            @click="setLanguage(lang.value)"
          >
            {{ lang.label }}
          </button>
        </div>
        <p class="center-text">Change theme / 更改主题</p>
        <div class="center-btns">
          <button
            v-for="theme in THEMES"
            :key="theme.value"
            class="btn btn-sm"
            :class="status.theme === theme.value ? 'btn-primary' : 'btn-adaptive'"
            @click="setTheme(theme.value)"
          >
            {{ theme.label }}
          </button>
        </div>
        <p class="center-text">
          Alas is a free open source software.
          <a href="https://github.com/LmeSzinc/AzurLaneAutoScript" target="_blank" rel="noreferrer">
            https://github.com/LmeSzinc/AzurLaneAutoScript
          </a>
        </p>
      </template>

      <!-- Update -->
      <template v-else-if="page === 'Update'">
        <div class="d-flex align-items-center gap-2 mb-3">
          <span class="badge" :class="`update-${updateState}`">{{ updateState }}</span>
          <button class="btn btn-sm btn-adaptive" :disabled="updateState === 'checking'" @click="checkUpdate">
            {{ t('Gui.Button.CheckUpdate') }}
          </button>
          <button
            class="btn btn-sm btn-primary"
            :disabled="updateState !== 'available'"
            @click="runUpdate"
          >
            {{ t('Gui.Button.Update') }}
          </button>
        </div>

        <table class="table table-sm compare-table">
          <thead>
            <tr>
              <th></th>
              <th>SHA1</th>
              <th>{{ t('Gui.Update.Author') }}</th>
              <th>{{ t('Gui.Update.Time') }}</th>
              <th>{{ t('Gui.Update.Message') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="history.local">
              <td>{{ t('Gui.Update.Local') }}</td>
              <td v-for="cell in history.local" :key="cell">{{ cell }}</td>
            </tr>
            <tr v-if="history.upstream">
              <td>{{ t('Gui.Update.Upstream') }}</td>
              <td v-for="cell in history.upstream" :key="cell">{{ cell }}</td>
            </tr>
          </tbody>
        </table>

        <p class="mb-1">{{ t('Gui.Update.DetailedHistory') }}</p>
        <table class="table table-sm history-table">
          <thead>
            <tr>
              <th>SHA1</th>
              <th>{{ t('Gui.Update.Author') }}</th>
              <th>{{ t('Gui.Update.Time') }}</th>
              <th>{{ t('Gui.Update.Message') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(commit, i) in history.history" :key="i">
              <td v-for="(cell, j) in commit" :key="j">{{ cell }}</td>
            </tr>
          </tbody>
        </table>
      </template>

      <!-- Remote -->
      <template v-else-if="page === 'Remote'">
        <p class="text-muted">未支持</p>
      </template>

      <!-- Utils -->
      <template v-else>
        <p class="text-muted">未实现</p>
      </template>
    </div>
  </div>
</template>

<style scoped>
.develop-wrap {
  height: 100%;
  display: flex;
  overflow: hidden;
}
.dev-menu {
  flex-shrink: 0;
  width: 12rem;
  padding: 1.2rem 0.5rem;
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
  text-align: left;
  cursor: pointer;
}
.btn-menu:hover,
.btn-menu-active {
  font-weight: bold;
  border-left-color: #4c9aff;
  color: #eaeaea;
}
.content {
  flex-grow: 1;
  padding: 1rem;
  overflow-y: auto;
}
.center-text {
  text-align: center;
  margin: 1rem 0 0.4rem;
}
.center-btns {
  display: flex;
  gap: 0.4rem;
  justify-content: center;
  flex-wrap: wrap;
}
.compare-table,
.history-table {
  color: #eaeaea;
}
.compare-table th,
.history-table th {
  color: #8a939c;
  font-weight: 500;
}
.update-idle,
.update-none {
  color: #8a939c;
}
.update-checking {
  color: #e6a23c;
}
.update-available {
  color: #4c9aff;
}
.update-updating {
  color: #4cd07d;
}
.update-failed {
  color: #e0645c;
}
</style>
