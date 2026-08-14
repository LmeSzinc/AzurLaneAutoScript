<script setup lang="ts">
import { computed } from 'vue'
import { t } from '@/api/i18n'
import type { ArgDefinition } from '@/api/types'

const props = defineProps<{
  args: Record<string, ArgDefinition>
  group: string
  task: string
  config: Record<string, unknown>
}>()

const emit = defineEmits<{
  save: [path: string, value: unknown]
}>()

interface Field {
  key: string
  def: ArgDefinition
  path: string
}

const fields = computed<Field[]>(() => {
  const result: Field[] = []
  for (const [key, def] of Object.entries(props.args)) {
    if (def.display === 'hide') continue
    result.push({
      key,
      def,
      path: `${props.task}.${props.group}.${key}`,
    })
  }
  return result
})

function currentValue(field: Field): unknown {
  const cur = (props.config[props.task] as Record<string, unknown>)?.[props.group]
  if (cur == null || typeof cur !== 'object') return field.def.value
  const v = (cur as Record<string, unknown>)[field.key]
  return v === undefined ? field.def.value : v
}

function emitSave(field: Field, value: unknown) {
  emit('save', field.path, value)
}

function label(field: Field): string {
  return t(`${props.group}.${field.key}.name`)
}

function helpLabel(field: Field): string | null {
  const key = `${props.group}.${field.key}.help`
  const text = t(key)
  return text !== key ? text : null
}

function asBool(field: Field): boolean {
  return currentValue(field) === true || currentValue(field) === 'True' || currentValue(field) === 1
}

/** datetime format: "YYYY-MM-DD HH:MM:SS" <-> datetime-local "YYYY-MM-DDTHH:MM" */
function toLocal(value: unknown): string {
  const s = String(value ?? '')
  return s.replace(' ', 'T').slice(0, 16)
}
function fromLocal(value: string): string {
  return value.replace('T', ' ') + ':00'
}

function isNumber(field: Field): boolean {
  const v = currentValue(field)
  return typeof v === 'number' || (typeof v === 'string' && v !== '' && !Number.isNaN(Number(v)))
}

/** storage values are dicts; edit them as JSON */
function storageText(field: Field): string {
  const v = currentValue(field)
  if (v == null || v === '') return ''
  if (typeof v === 'string') {
    try {
      return JSON.stringify(JSON.parse(v), null, 2)
    } catch {
      return v
    }
  }
  return JSON.stringify(v, null, 2)
}

function parseStorage(text: string): unknown {
  const trimmed = text.trim()
  if (!trimmed) return {}
  try {
    return JSON.parse(trimmed)
  } catch {
    return text
  }
}

function selectOptions(field: Field): string[] {
  return (field.def.option as string[]) ?? []
}

function optionLabel(field: Field, opt: string): string {
  return t(`${props.group}.${field.key}.${opt}`)
}
</script>

<template>
  <div class="dynamic-form">
    <div v-for="field in fields" :key="field.key" class="form-field">
      <!-- title column: title on top, help below -->
      <div class="field-title-col">
        <div class="field-title">{{ label(field) }}</div>
        <small v-if="helpLabel(field)" class="field-help">{{ helpLabel(field) }}</small>
      </div>

      <!-- control column -->
      <div class="field-control">
        <!-- select -->
        <select
          v-if="field.def.type === 'select'"
          class="form-control form-control-sm"
          :value="currentValue(field)"
          :disabled="field.def.display === 'disabled'"
          @change="emitSave(field, ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="opt in selectOptions(field)" :key="opt" :value="opt">
            {{ optionLabel(field, opt) }}
          </option>
        </select>

        <!-- checkbox -->
        <div v-else-if="field.def.type === 'checkbox'" class="form-check">
          <input
            class="form-check-input"
            type="checkbox"
            :checked="asBool(field)"
            :disabled="field.def.display === 'disabled'"
            @change="emitSave(field, ($event.target as HTMLInputElement).checked)"
          />
        </div>

        <!-- datetime -->
        <input
          v-else-if="field.def.type === 'datetime'"
          class="form-control form-control-sm"
          type="datetime-local"
          :value="toLocal(currentValue(field))"
          :disabled="field.def.display === 'disabled'"
          @change="emitSave(field, fromLocal(($event.target as HTMLInputElement).value))"
        />

        <!-- storage: dict edited as JSON -->
        <textarea
          v-else-if="field.def.type === 'storage'"
          class="form-control form-control-sm"
          rows="4"
          :value="storageText(field)"
          :disabled="field.def.display === 'disabled'"
          @change="emitSave(field, parseStorage(($event.target as HTMLTextAreaElement).value))"
        />

        <!-- textarea -->
        <textarea
          v-else-if="field.def.type === 'textarea'"
          class="form-control form-control-sm"
          rows="3"
          :value="String(currentValue(field) ?? '')"
          :disabled="field.def.display === 'disabled'"
          @change="emitSave(field, ($event.target as HTMLTextAreaElement).value)"
        />

        <!-- state / lock: read-only display -->
        <div v-else-if="field.def.type === 'state' || field.def.type === 'lock'" class="form-control-plaintext">
          {{ currentValue(field) }}
        </div>

        <!-- default: input (number or text) -->
        <input
          v-else
          class="form-control form-control-sm"
          :type="isNumber(field) ? 'number' : 'text'"
          :value="String(currentValue(field) ?? '')"
          :disabled="field.def.display === 'disabled'"
          @change="emitSave(field, ($event.target as HTMLInputElement).value)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.form-field {
  display: grid;
  grid-template-columns: 1fr 13rem;
  align-items: center;
  margin: 0.125rem 0;
}
.field-title-col {
  padding-right: 0.5rem;
}
.field-title {
  font-size: 1rem;
  font-weight: 500;
  margin: 0 0.25rem;
  overflow-wrap: break-word;
  color: #eaeaea;
}
.field-help {
  display: block;
  font-size: 0.8rem;
  margin: 0.2rem 0.25rem 0.1rem;
  overflow-wrap: break-word;
  color: #8a939c;
}
.field-control {
  padding-right: 0.25rem;
}
.form-control {
  background: #1d2226;
  border-color: #39424a;
  color: #eaeaea;
}
.form-check {
  margin: 0;
  text-align: center;
}
</style>
