/** Instance state: 1 running, 2 inactive, 3 warning, 4 updating */
export type InstanceState = 1 | 2 | 3 | 4

export interface InstanceStatus {
  name: string
  state: InstanceState
  alive: boolean
}

export interface Status {
  instances: InstanceStatus[]
  theme: string
  language: string
}

/** Payload of the `log` server-sent event. */
export interface SseLog {
  instance: string
  logs: string[]
  reset?: boolean
}

export interface SchedulerTask {
  command: string
  next_run: string
}

/** Live scheduler snapshot pushed from the bot process (SSE `scheduler` event). */
export interface SchedulerSnapshot {
  current: string | null
  pending: SchedulerTask[]
  waiting: SchedulerTask[]
}

/** Config schema: task -> group -> arg -> definition */
export interface ArgDefinition {
  type: string
  value?: unknown
  valuetype?: string
  validate?: string
  /** select options; values may be strings, numbers or booleans */
  option?: unknown[]
  option_bold?: unknown[]
  option_light?: unknown[]
  display?: string
  help?: string
  [key: string]: unknown
}

export type ArgSchema = Record<string, Record<string, Record<string, ArgDefinition>>>

export interface MenuTask {
  page?: string
  menu?: string
  tasks?: string[]
}

export interface MenuSchema {
  [menu: string]: MenuTask
}
