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

export interface LogEvent {
  type: 'log'
  data: {
    instance: string
    logs: string[]
  }
}

export interface StatusEvent {
  type: 'status'
  data: Status
}

export type WsEvent = StatusEvent | LogEvent

/** Config schema: task -> group -> arg -> definition */
export interface ArgDefinition {
  type: string
  value?: unknown
  valuetype?: string
  validate?: string
  option?: string[]
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
