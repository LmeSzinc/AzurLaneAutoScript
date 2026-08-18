<script lang="ts">
import { t } from "../api/i18n.svelte";
import type { ArgDefinition } from "../api/types";

let {
  args,
  group,
  task,
  config,
  onsave,
}: {
  args: Record<string, ArgDefinition>;
  group: string;
  task: string;
  config: Record<string, unknown>;
  onsave?: (path: string, value: unknown) => void;
} = $props();

interface Field {
  key: string;
  def: ArgDefinition;
  path: string;
}

const fields = $derived.by<Field[]>(() => {
  const result: Field[] = [];
  for (const [key, def] of Object.entries(args)) {
    if (def.display === "hide") continue;
    result.push({
      key,
      def,
      path: `${task}.${group}.${key}`,
    });
  }
  return result;
});

function currentValue(field: Field): unknown {
  const cur = (config[task] as Record<string, unknown> | undefined)?.[group];
  if (cur == null || typeof cur !== "object") return field.def.value;
  const v = (cur as Record<string, unknown>)[field.key];
  return v === undefined ? field.def.value : v;
}

function emitSave(field: Field, value: unknown) {
  onsave?.(field.path, value);
}

function label(field: Field): string {
  return t(`${group}.${field.key}.name`);
}

function helpLabel(field: Field): string | null {
  const key = `${group}.${field.key}.help`;
  const text = t(key);
  return text !== key ? text : null;
}

function asBool(field: Field): boolean {
  const v = currentValue(field);
  return v === true || v === "True" || v === 1;
}

/** datetime format: "YYYY-MM-DD HH:MM:SS" <-> datetime-local "YYYY-MM-DDTHH:MM" */
function toLocal(value: unknown): string {
  const s = String(value ?? "");
  return s.replace(" ", "T").slice(0, 16);
}
function fromLocal(value: string): string {
  // Empty input resets the arg to its default (e.g. Scheduler.NextRun ->
  // 2020-01-01, i.e. run immediately)
  if (!value) return "";
  return value.replace("T", " ") + ":00";
}

function isNumber(field: Field): boolean {
  const v = currentValue(field);
  return typeof v === "number" || (typeof v === "string" && v !== "" && !Number.isNaN(Number(v)));
}

/** storage values are dicts; edit them as JSON */
function storageText(field: Field): string {
  const v = currentValue(field);
  if (v == null || v === "") return "";
  if (typeof v === "string") {
    try {
      return JSON.stringify(JSON.parse(v), null, 2);
    } catch {
      return v;
    }
  }
  return JSON.stringify(v, null, 2);
}

function parseStorage(text: string): unknown {
  const trimmed = text.trim();
  if (!trimmed) return {};
  try {
    return JSON.parse(trimmed);
  } catch {
    return text;
  }
}

function selectOptions(field: Field): unknown[] {
  return (field.def.option as unknown[]) ?? [];
}

function optionLabel(field: Field, opt: string): string {
  return t(`${group}.${field.key}.${opt}`);
}

/** state/lock values render translated option labels ("已启用" / event names) */
function stateText(field: Field): string {
  const v = currentValue(field);
  if (typeof v === "boolean") {
    return t(`${group}.${field.key}.${v ? "True" : "False"}`);
  }
  const opt = String(v ?? "");
  const key = `${group}.${field.key}.${opt}`;
  const label = t(key);
  return label !== key ? label : opt;
}

/** original dark theme styles state values in option_bold/option_light */
function stateClass(field: Field): string {
  const v = currentValue(field);
  const bold = field.def.option_bold?.includes(v as never);
  const light = field.def.option_light?.includes(v as never);
  return bold ? "state-bold" : light ? "state-light" : "";
}
</script>

<div>
  {#each fields as field (field.key)}
    <div
      class="grid [grid-auto-flow:column] [grid-template-columns:1fr_13rem] items-center {field.def.type === 'checkbox' ||
      field.def.type === 'storage'
        ? 'arg-container-checkbox'
        : 'arg-container'}"
    >
      <!-- title column: title on top, help below -->
      <div class="pr-2">
        <div class="arg-title">{label(field)}</div>
        {#if helpLabel(field)}
          <div class="arg-help">{helpLabel(field)}</div>
        {/if}
      </div>

      <!-- control column -->
      <div class="m-0 pr-1">
        {#if field.def.type === 'select'}
          <select
            class="form-control appearance-none [-webkit-appearance:none] [-moz-appearance:none] !pr-4 [background-position:right,center] [background-repeat:no-repeat]"
            value={String(currentValue(field) ?? '')}
            disabled={field.def.display === 'disabled'}
            onchange={(e) => emitSave(field, (e.currentTarget as HTMLSelectElement).value)}
          >
            {#each selectOptions(field) as opt (opt)}
              <option value={String(opt)}>{optionLabel(field, String(opt))}</option>
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
          <div class="state-display {stateClass(field)}">{stateText(field)}</div>
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
