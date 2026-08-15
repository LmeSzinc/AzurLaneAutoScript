<script lang="ts">
  import { t } from '../api/i18n.svelte'
  import type { ArgDefinition } from '../api/types'

  let {
    args,
    group,
    task,
    config,
    onsave,
  }: {
    args: Record<string, ArgDefinition>
    group: string
    task: string
    config: Record<string, unknown>
    onsave?: (path: string, value: unknown) => void
  } = $props()

  interface Field {
    key: string
    def: ArgDefinition
    path: string
  }

  const fields = $derived.by<Field[]>(() => {
    const result: Field[] = []
    for (const [key, def] of Object.entries(args)) {
      if (def.display === 'hide') continue
      result.push({
        key,
        def,
        path: `${task}.${group}.${key}`,
      })
    }
    return result
  })

  function currentValue(field: Field): unknown {
    const cur = (config[task] as Record<string, unknown> | undefined)?.[group]
    if (cur == null || typeof cur !== 'object') return field.def.value
    const v = (cur as Record<string, unknown>)[field.key]
    return v === undefined ? field.def.value : v
  }

  function emitSave(field: Field, value: unknown) {
    onsave?.(field.path, value)
  }

  function label(field: Field): string {
    return t(`${group}.${field.key}.name`)
  }

  function helpLabel(field: Field): string | null {
    const key = `${group}.${field.key}.help`
    const text = t(key)
    return text !== key ? text : null
  }

  function asBool(field: Field): boolean {
    const v = currentValue(field)
    return v === true || v === 'True' || v === 1
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
    return t(`${group}.${field.key}.${opt}`)
  }

  /** state/lock values render translated booleans ("已启用" instead of "true") */
  function stateText(field: Field): string {
    const v = currentValue(field)
    if (typeof v === 'boolean') {
      return t(`${group}.${field.key}.${v ? 'True' : 'False'}`)
    }
    return String(v ?? '')
  }
</script>

<div class="dynamic-form">
  {#each fields as field (field.key)}
    <div
      class="form-field {field.def.type === 'checkbox' || field.def.type === 'storage'
        ? 'arg-container-checkbox'
        : 'arg-container'}"
    >
      <!-- title column: title on top, help below -->
      <div class="field-title-col">
        <div class="arg-title">{label(field)}</div>
        {#if helpLabel(field)}
          <div class="arg-help">{helpLabel(field)}</div>
        {/if}
      </div>

      <!-- control column -->
      <div class="field-control arg-input">
        {#if field.def.type === 'select'}
          <select
            class="form-control"
            value={String(currentValue(field) ?? '')}
            disabled={field.def.display === 'disabled'}
            onchange={(e) => emitSave(field, (e.currentTarget as HTMLSelectElement).value)}
          >
            {#each selectOptions(field) as opt (opt)}
              <option value={opt}>{optionLabel(field, opt)}</option>
            {/each}
          </select>
        {:else if field.def.type === 'checkbox'}
          <div class="form-check">
            <input
              class="form-check-input"
              type="checkbox"
              checked={asBool(field)}
              disabled={field.def.display === 'disabled'}
              onchange={(e) => emitSave(field, (e.currentTarget as HTMLInputElement).checked)}
            />
          </div>
        {:else if field.def.type === 'datetime'}
          <input
            class="form-control"
            type="datetime-local"
            value={toLocal(currentValue(field))}
            disabled={field.def.display === 'disabled'}
            onchange={(e) => emitSave(field, fromLocal((e.currentTarget as HTMLInputElement).value))}
          />
        {:else if field.def.type === 'storage'}
          <textarea
            class="form-control"
            rows="4"
            value={storageText(field)}
            disabled={field.def.display === 'disabled'}
            onchange={(e) => emitSave(field, parseStorage((e.currentTarget as HTMLTextAreaElement).value))}></textarea>
        {:else if field.def.type === 'textarea'}
          <textarea
            class="form-control"
            rows="3"
            value={String(currentValue(field) ?? '')}
            disabled={field.def.display === 'disabled'}
            onchange={(e) => emitSave(field, (e.currentTarget as HTMLTextAreaElement).value)}></textarea>
        {:else if field.def.type === 'state' || field.def.type === 'lock'}
          <div class="state-display">{stateText(field)}</div>
        {:else}
          <input
            class="form-control"
            type={isNumber(field) ? 'number' : 'text'}
            value={String(currentValue(field) ?? '')}
            disabled={field.def.display === 'disabled'}
            onchange={(e) => emitSave(field, (e.currentTarget as HTMLInputElement).value)}
          />
        {/if}
      </div>
    </div>
  {/each}
</div>

<style>
  /* PC layout from alas-pc.css: title column + 13rem control column */
  .form-field {
    display: grid;
    grid-auto-flow: column;
    grid-template-columns: 1fr 13rem;
    align-items: center;
  }
  .field-title-col {
    padding-right: 0.5rem;
  }
  /* state/lock: bordered on top/left/right, no bottom line */
  .state-display {
    border: 1px solid #6c757d;
    border-bottom: 0;
    padding: 0 0.5rem;
    height: auto;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
</style>
