import { reactive } from 'vue'
import { api } from './client'
import { status } from './store'

const dicts = reactive<Record<string, Record<string, string>>>({})

/**
 * Load the dictionary for the currently active language.
 * The language follows status.language, which is refreshed from the backend.
 */
export async function loadI18n(): Promise<Record<string, string>> {
  const lang = status.language || 'zh-CN'
  if (!dicts[lang]) {
    dicts[lang] = await api.i18n(lang)
  }
  return dicts[lang]
}

/** Translate a dotted key, e.g. "Gui.Overview.Scheduler". */
export function t(key: string): string {
  const dict = dicts[status.language] ?? dicts['zh-CN']
  if (!dict) return key
  return dict[key] ?? key
}
