import { api } from './client'
import type { Status, SseLog } from './types'

const BASE = import.meta.env.VITE_API_BASE ?? ''

export const status = $state<Status>({
  instances: [],
  theme: 'dark',
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

let es: EventSource | null = null
let reconnectTimer: number | undefined

export function connectEvents() {
  if (es) {
    return
  }
  const url = `${BASE}/sse`
  es = new EventSource(url)
  es.onopen = () => {
    connState.connected = true
  }
  es.addEventListener('status', (event) => {
    Object.assign(status, JSON.parse((event as MessageEvent<string>).data) as Status)
  })
  es.addEventListener('log', (event) => {
    const { instance, logs: newLogs, reset } = JSON.parse((event as MessageEvent<string>).data) as SseLog
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
  })
  es.onerror = () => {
    connState.connected = false
    es?.close()
    es = null
    reconnectTimer = window.setTimeout(connectEvents, 2000)
  }
}

export function disconnectEvents() {
  window.clearTimeout(reconnectTimer)
  es?.close()
  es = null
}
