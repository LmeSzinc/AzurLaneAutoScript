import type {LocaleSetting, LocaleType} from '/#/config';

export const LOCALE: {[key: string]: LocaleType} = {
  ZH_CN: 'zh-CN',
  EN_US: 'en-US',
  JA_JP: 'ja-JP',
  ZH_TW: 'zh-TW',
  ES_ES: 'es-ES',
};

// locale list
export const localeList: {label: string; value: keyof typeof LOCALE}[] = [
  {
    label: '简体中文',
    value: LOCALE.ZH_CN,
  },
  {
    label: 'English',
    value: LOCALE.EN_US,
  },
  {
    label: '日本語',
    value: LOCALE.JA_JP,
  },
  {
    label: '繁體中文',
    value: LOCALE.ZH_TW,
  },
  {
    label: 'Español',
    value: LOCALE.ES_ES,
  },
];

export const localeSetting: LocaleSetting = {
  showPicker: true,
  // Locale
  locale: LOCALE.EN_US,
  // Default locale
  fallback: LOCALE.JA_JP,
  // available Locales
  availableLocales: [LOCALE.ZH_CN, LOCALE.EN_US, LOCALE.JA_JP, LOCALE.ZH_TW, LOCALE.ES_ES],
};
