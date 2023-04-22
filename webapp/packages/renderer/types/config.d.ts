z;
/**
 * 'zh-CN' | 'en-US' | 'ja-JP' | 'zh-TW'
 */
export type LocaleType = 'zh-CN' | 'en-US' | 'ja-JP' | 'zh-TW';

export interface LocaleSetting {
  showPicker: boolean;
  // Current language
  locale: LocaleType;
  // default language
  fallback: LocaleType;
  // available Locales
  availableLocales: LocaleType[];
}

export interface OptionItem {
  value: string;
  label: string;
}
