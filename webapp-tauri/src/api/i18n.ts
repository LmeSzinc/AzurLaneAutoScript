import { reactive } from 'vue'
import { api } from './client'

const dicts = reactive<Record<string, Record<string, string>>>({})

export const currentLang = 'zh-CN'

export async function loadI18n(lang: string) {
  if (!dicts[lang]) {
    dicts[lang] = await api.i18n(lang)
  }
  return dicts[lang]
}

/** Translate a dotted key, e.g. "Gui.Overview.Scheduler". */
export function t(key: string, lang = currentLang): string {
  const dict = dicts[lang]
  if (!dict) return key
  return dict[key] ?? key
}
