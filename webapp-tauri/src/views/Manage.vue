<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api/client'
import { loadI18n, t } from '@/api/i18n'
import { refreshStatus } from '@/api/store'
import AppAside from '@/components/AppAside.vue'

const router = useRouter()

interface ConfigFile {
  name: string
  modified: string
}

const configs = ref<ConfigFile[]>([])
const newName = ref('')
const error = ref('')
const fileInput = ref<HTMLInputElement | null>(null)

async function refresh() {
  configs.value = await api.configs()
}

async function createConfig() {
  error.value = ''
  const res = await api.newInstance(newName.value)
  if (!res.ok) {
    error.value = res.error ?? 'Failed'
    return
  }
  newName.value = ''
  await refresh()
  await refreshStatus()
}

function pickImportFile() {
  fileInput.value?.click()
}

async function importFile(event: Event) {
  error.value = ''
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  const text = await file.text()
  let config: Record<string, unknown>
  try {
    config = JSON.parse(text)
  } catch {
    error.value = 'Invalid JSON file'
    return
  }
  const name = file.name.replace(/\.json$/, '')
  await api.importConfig(name, config)
  input.value = ''
  await refresh()
  await refreshStatus()
}

async function exportConfig(name: string) {
  const res = await fetch(`/config/${name}/export`)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${name}.json`
  a.click()
  URL.revokeObjectURL(url)
}

function onAsideSelect(name: string) {
  if (name === 'Manage') {
    return
  }
  if (name === 'Home') {
    router.push('/develop')
    return
  }
  router.push('/')
}

onMounted(async () => {
  void loadI18n('zh-CN')
  await refreshStatus()
  await refresh()
})
</script>

<template>
  <div class="manage-wrap">
    <AppAside active="Manage" @select="onAsideSelect" />
    <div class="content">
      <h4>{{ t('Gui.AppManage.Title') }}</h4>
      <div v-if="error" class="alert alert-danger">{{ error }}</div>

      <table class="table table-sm config-table">
        <thead>
          <tr>
            <th>{{ t('Gui.AppManage.Name') }}</th>
            <th>{{ t('Gui.AppManage.Modified') }}</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="cfg in configs" :key="cfg.name">
            <td>{{ cfg.name }}</td>
            <td>{{ cfg.modified }}</td>
            <td class="text-end">
              <button class="btn btn-sm btn-outline-light" @click="exportConfig(cfg.name)">
                {{ t('Gui.AppManage.Export') }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="d-flex gap-2 mt-3 align-items-center">
        <input v-model="newName" class="form-control form-control-sm" style="max-width: 220px" placeholder="config name" />
        <button class="btn btn-sm btn-success" :disabled="!newName" @click="createConfig">
          {{ t('Gui.AppManage.Add') }}
        </button>
        <button class="btn btn-sm btn-outline-light" @click="pickImportFile">
          {{ t('Gui.AppManage.Import') }}
        </button>
        <input ref="fileInput" type="file" accept=".json" style="display: none" @change="importFile" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.manage-wrap {
  height: 100%;
  display: flex;
  overflow: hidden;
}
.content {
  flex-grow: 1;
  padding: 1rem;
  overflow-y: auto;
}
.config-table {
  max-width: 640px;
}
.config-table th {
  color: #8a939c;
  font-weight: 500;
}
</style>
