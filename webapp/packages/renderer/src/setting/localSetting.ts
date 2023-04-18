import type {LocaleType} from '/#/config';

export const LOCALE: {[key: string]: LocaleType} = {
  ZH_CN: 'zh-CN',
  EN_US: 'en-US',
  JA_JP: 'ja-JP',
  ZH_TW: 'zh-TW',
};

// locale list
export const localeList: {text: string; event: keyof typeof LOCALE}[] = [
  {
    text: '简体中文',
    event: LOCALE.ZH_CN,
  },
  {
    text: 'English',
    event: LOCALE.EN_US,
  },
  {
    text: '日本語',
    event: LOCALE.JA_JP,
  },
  {
    text: '繁體中文',
    event: LOCALE.ZH_TW,
  },
];
