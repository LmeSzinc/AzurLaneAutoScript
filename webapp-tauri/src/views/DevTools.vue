<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api/client'
import { refreshStatus, status } from '@/api/store'
import AppAside from '@/components/AppAside.vue'

const router = useRouter()

function onAsideSelect(name: string) {
  if (name === 'Manage') {
    return
  }
  // Home or an instance: both lead to the overview page
  router.push('/')
}

const updateState = ref('idle')
const currentCommit = ref<{ sha: string; message: string } | null>(null)
const newName = ref('')
const origin = ref('template')
const error = ref('')
const remote = ref({ alive: false, state: '', entry_point: '' })

async function refreshUpdate() {
  const res = await api.updateStatus()
  updateState.value = res.state
  currentCommit.value = res.current
}

async function refreshRemote() {
  remote.value = await api.remoteStatus()
}

async function checkUpdate() {
  await api.updateCheck()
  // Poll until the check finishes
  const timer = window.setInterval(async () => {
    await refreshUpdate()
    if (updateState.value !== 'checking') {
      window.clearInterval(timer)
    }
  }, 1500)
}

async function runUpdate() {
  await api.updateRun()
  const timer = window.setInterval(async () => {
    await refreshUpdate()
    if (updateState.value !== 'updating') {
      window.clearInterval(timer)
    }
  }, 2000)
}

async function createInstance() {
  error.value = ''
  const res = await api.newInstance(newName.value, origin.value || undefined)
  if (!res.ok) {
    error.value = res.error ?? 'Failed'
    return
  }
  newName.value = ''
  await refreshStatus()
}

async function deleteInstance(name: string) {
  error.value = ''
  if (!window.confirm(`Delete instance "${name}"?`)) return
  const res = await api.deleteInstance(name)
  if (!res.ok) {
    error.value = res.error ?? 'Failed'
    return
  }
  await refreshStatus()
}

onMounted(() => {
  void refreshUpdate()
  void refreshStatus()
  void refreshRemote()
})
</script>

<template>
  <div class="devtools-wrap">
    <AppAside active="Manage" @select="onAsideSelect" />
    <div class="devtools container-fluid">
    <div class="row">
      <div class="col-md-6">
        <div class="card">
          <div class="card-header">Updater</div>
          <div class="card-body">
            <p>
              Current:
              <code v-if="currentCommit">{{ currentCommit.sha }} {{ currentCommit.message }}</code>
              <code v-else>unknown</code>
            </p>
            <p>
              State: <span class="badge" :class="`update-${updateState}`">{{ updateState }}</span>
            </p>
            <div class="btn-group">
              <button class="btn btn-sm btn-outline-light" :disabled="updateState === 'checking'" @click="checkUpdate">
                Check update
              </button>
              <button
                class="btn btn-sm btn-primary"
                :disabled="updateState !== 'available'"
                @click="runUpdate"
              >
                Update
              </button>
            </div>
          </div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card">
          <div class="card-header">Instances</div>
          <div class="card-body">
            <div v-if="error" class="alert alert-danger">{{ error }}</div>
            <ul class="list-group mb-3">
              <li v-for="inst in status.instances" :key="inst.name" class="list-group-item d-flex justify-content-between">
                <span>{{ inst.name }}</span>
                <button
                  v-if="inst.name !== 'alas'"
                  class="btn btn-sm btn-outline-danger"
                  @click="deleteInstance(inst.name)"
                >
                  Delete
                </button>
              </li>
            </ul>
            <div class="input-group input-group-sm">
              <input v-model="newName" class="form-control" placeholder="New instance name" />
              <select v-model="origin" class="form-control">
                <option value="template">template</option>
                <option v-for="inst in status.instances" :key="inst.name" :value="inst.name">{{ inst.name }}</option>
              </select>
              <button class="btn btn-sm btn-success" :disabled="!newName" @click="createInstance">Create</button>
            </div>
          </div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card">
          <div class="card-header">Remote access</div>
          <div class="card-body">
            <p>
              Status: <span class="badge" :class="remote.alive ? 'update-updating' : 'update-none'">{{ remote.alive ? 'alive' : 'stopped' }}</span>
            </p>
            <p v-if="remote.entry_point">Entry point: <code>{{ remote.entry_point }}</code></p>
            <div class="btn-group">
              <button class="btn btn-sm btn-success" :disabled="remote.alive" @click="api.remoteStart().then(refreshRemote)">
                Start
              </button>
              <button class="btn btn-sm btn-outline-danger" :disabled="!remote.alive" @click="api.remoteStop().then(refreshRemote)">
                Stop
              </button>
            </div>
          </div>
        </div>
      </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.devtools-wrap {
  height: 100%;
  display: flex;
  overflow: hidden;
}
.devtools {
  flex-grow: 1;
  padding: 16px;
  overflow-y: auto;
}
.card {
  background: #23292e;
  border-color: #39424a;
  margin-bottom: 14px;
}
.card-header {
  background: #2a3137;
  color: #eaeaea;
  font-weight: 600;
}
.card-body {
  color: #cfd4d9;
}
.list-group-item {
  background: transparent;
  color: #eaeaea;
  border-color: #39424a;
}
.update-checking {
  color: #e6a23c;
}
.update-available {
  color: #4c9aff;
}
.update-none,
.update-idle,
.update-done {
  color: #8a939c;
}
.update-updating {
  color: #4cd07d;
}
.update-error {
  color: #e0645c;
}
</style>
