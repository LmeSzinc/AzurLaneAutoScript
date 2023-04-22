import zh_CN from '/@/locales/lang/zh_CN';
import en_US from '/@/locales/lang/en_US';
import ja_JP from '/@/locales/lang/ja_JP';
import zh_TW from '/@/locales/lang/zh_TW';
import type {LocaleType} from '/#/config';

export const LocaleMap: {[k in LocaleType]: any} = {
  'zh-CN': zh_CN,
  'en-US': en_US,
  'ja-JP': ja_JP,
  'zh-TW': zh_TW,
};
