import {LOCALE} from '/@/setting/localSetting';
import type {DefSetting} from '/#/config';

export const defSetting: DefSetting = {
  // Locale
  locale: window.__electron_preload__getAlasConfig().language || LOCALE.ZH_CN,
  // theme
  theme: window.__electron_preload__getAlasConfig().theme || 'dark',
  // Default locale
  fallback: LOCALE.ZH_CN,
  // available Locales
  availableLocales: [LOCALE.ZH_CN, LOCALE.EN_US, LOCALE.JA_JP, LOCALE.ZH_TW],

  repository: '',
};
