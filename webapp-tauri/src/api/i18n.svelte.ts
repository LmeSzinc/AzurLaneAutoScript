import { api } from "./client";
import { status } from "./store.svelte";

const dicts = $state<Record<string, Record<string, string>>>({});

/**
 * Load the dictionary for the currently active language.
 * The language follows status.language, which is refreshed from the backend.
 */
export async function loadI18n(): Promise<Record<string, string>> {
  const lang = status.language || "zh-CN";
  const dict = (dicts[lang] ??= await api.i18n(lang));
  return dict;
}

/** Translate a dotted key, e.g. "Gui.Overview.Scheduler".
 *  Named placeholders like {name} in the template are substituted from
 *  `args` when provided (same convention as the backend `.format`). */
export function t(key: string, args?: Record<string, string | number>): string {
  const dict = dicts[status.language] ?? dicts["zh-CN"];
  const template = dict?.[key] ?? key;
  if (!args) return template;
  return template.replace(/\{(\w+)\}/g, (match, name: string) =>
    args[name] !== undefined ? String(args[name]) : match,
  );
}
