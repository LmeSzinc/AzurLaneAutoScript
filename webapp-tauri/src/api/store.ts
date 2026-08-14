import { reactive, ref } from 'vue'
import { api } from '../api/client'
import type { Status } from '../api/types'

const BASE = import.meta.env.VITE_API_BASE ?? ''

function wsUrl(): string {
  if (BASE) {
    return BASE.replace(/^http/, 'ws')
  }
  const scheme = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${scheme}//${window.location.host}`
}

export const status = reactive<Status>({
  instances: [],
  theme: 'default',
  language: 'zh-CN',
})

export const connected = ref(false)

/** Per-instance log buffer, newest entries last. */
export const logs = reactive<Record<string, string[]>>({})

/** Shared menu collapse state so it survives page navigation. */
export const collapsedGroups = reactive<Record<string, boolean>>({})

/** Explicit page title set by pages (e.g. the develop sub pages). */
export const pageTitle = ref('')

export async function refreshStatus() {
  Object.assign(status, await api.status())
}

let ws: WebSocket | null = null
let reconnectTimer: number | undefined

export function connectWs() {
  if (ws) {
    return
  }
  const url = wsUrl() + '/ws'
  ws = new WebSocket(url)
  ws.onopen = () => {
    connected.value = true
  }
  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data as string)
    if (msg.type === 'status') {
      Object.assign(status, msg.data)
    } else if (msg.type === 'log') {
      const { instance, logs: newLogs } = msg.data
      const buf = logs[instance] ?? (logs[instance] = [])
      buf.push(...newLogs)
      if (buf.length > 500) {
        buf.splice(0, buf.length - 500)
      }
    }
  }
  ws.onclose = () => {
    connected.value = false
    ws = null
    reconnectTimer = window.setTimeout(connectWs, 2000)
  }
  ws.onerror = () => {
    ws?.close()
  }
}

export function disconnectWs() {
  window.clearTimeout(reconnectTimer)
  ws?.close()
  ws = null
}
