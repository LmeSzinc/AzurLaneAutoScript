import { api } from './client'
import type { Status } from './types'

const BASE = import.meta.env.VITE_API_BASE ?? ''

function wsUrl(): string {
  if (BASE) {
    return BASE.replace(/^http/, 'ws')
  }
  const scheme = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${scheme}//${window.location.host}`
}

export const status = $state<Status>({
  instances: [],
  theme: 'default',
  language: 'zh-CN',
})

/** WS connection state (wrapped so the property may be reassigned). */
export const connState = $state<{ connected: boolean }>({ connected: false })

/** Per-instance log buffer, newest entries last. */
export const logs = $state<Record<string, string[]>>({})

/** Shared menu collapse state so it survives page navigation. */
export const collapsedGroups = $state<Record<string, boolean>>({})

/** Explicit page title set by pages (e.g. the develop sub pages). */
export const titleState = $state<{ value: string }>({ value: '' })

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
    connState.connected = true
  }
  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data as string)
    if (msg.type === 'status') {
      Object.assign(status, msg.data)
    } else if (msg.type === 'log') {
      const { instance, logs: newLogs, reset } = msg.data as { instance: string; logs: string[]; reset?: boolean }
      if (reset) {
        // Backend re-sent the whole buffer (initial connect / backend trim).
        // Replace the array identity so LogView rebuilds.
        logs[instance] = [...newLogs]
      } else {
        const buf = (logs[instance] ??= [])
        buf.push(...newLogs)
        if (buf.length > 800) {
          // Trim in chunks with identity replacement so LogView rebuilds
          // rarely (every ~300 lines) instead of re-rendering every second.
          logs[instance] = buf.slice(-500)
        }
      }
    }
  }
  ws.onclose = () => {
    connState.connected = false
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
