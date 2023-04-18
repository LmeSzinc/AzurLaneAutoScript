import type {AlasConfig} from '../../preload/src/alasConfig';

/**
 * 'zh-CN' | 'en-US' | 'ja-JP' | 'zh-TW'
 */
export type LocaleType = 'zh-CN' | 'en-US' | 'ja-JP' | 'zh-TW';

export interface DefSetting {
  // Current language
  locale: LocaleType;
  //Current theme
  theme: AlasConfig['theme'];
  // default language
  fallback: LocaleType;
  // available Locales
  availableLocales: LocaleType[];
  // repository
  repository: string;
}

export interface OptionItem {
  value: string;
  label: string;
}
