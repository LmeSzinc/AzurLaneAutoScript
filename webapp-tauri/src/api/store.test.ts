import { afterEach, describe, expect, it, vi } from 'vitest'

class MockEventSource {
  static instances: MockEventSource[] = []
  url: string
  onopen: ((ev: Event) => void) | null = null
  onerror: ((ev: Event) => void) | null = null
  private listeners = new Map<string, ((e: MessageEvent) => void)[]>()

  constructor(url: string) {
    this.url = url
    MockEventSource.instances.push(this)
  }

  addEventListener(type: string, cb: (e: MessageEvent) => void) {
    const list = this.listeners.get(type) ?? []
    list.push(cb)
    this.listeners.set(type, list)
  }

  dispatch(type: string, data: unknown) {
    const ev = { data: JSON.stringify(data) } as MessageEvent
    for (const cb of this.listeners.get(type) ?? []) {
      cb(ev)
    }
  }

  close() {}
}

import { connectEvents, disconnectEvents, schedulers } from './store.svelte'

describe('SSE scheduler events', () => {
  afterEach(() => {
    disconnectEvents()
    vi.unstubAllGlobals()
    MockEventSource.instances = []
  })

  it('updates the schedulers store from a scheduler event', () => {
    vi.stubGlobal('EventSource', MockEventSource)
    connectEvents()
    const es = MockEventSource.instances[0]
    expect(es.url.endsWith('/sse')).toBe(true)

    es.dispatch('scheduler', {
      instance: 'alas',
      current: 'Commission',
      pending: [
        { command: 'Commission', next_run: '2026-08-16 14:32:26' },
        { command: 'Research', next_run: '2026-08-16 16:32:27' },
      ],
      waiting: [{ command: 'Restart', next_run: '2026-08-17 00:00:00' }],
    })

    expect(schedulers['alas']?.current).toBe('Commission')
    expect(schedulers['alas']?.pending).toHaveLength(2)
    expect(schedulers['alas']?.pending[1].command).toBe('Research')
    expect(schedulers['alas']?.waiting[0].command).toBe('Restart')
  })
})
