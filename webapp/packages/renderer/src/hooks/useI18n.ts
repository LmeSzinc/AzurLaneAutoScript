import {i18n} from '/@/locales/setupI18n';

export interface I18nGlobalTranslation {
  (key: string): string;
  (key: string, locale?: string): string;
  (key: string, locale?: string, list?: unknown[]): string;
  (key: string, locale?: string, named?: Record<string, unknown>): string;
  (key: string, list?: unknown[]): string;
  (key: string, named?: Record<string, unknown>): string;
}

type I18nTranslationRestParameters = [string, any];

function getKey(namespace: string | undefined, key: string): string {
  if (!namespace) {
    return key;
  }
  if (key.startsWith(namespace)) {
    return key;
  }
  return `${namespace}.${key}`;
}

export function useI18n(namespace?: string) {
  const normalFn = {
    t: (key: string) => {
      return getKey(namespace, key);
    },
  };
  if (!i18n) {
    return normalFn;
  }

  const {t, ...methods} = i18n.global;

  const tFn: I18nGlobalTranslation = (key: string, ...arg: any[]) => {
    if (!key) return '';
    if (!key.includes('.') && !namespace) return key;
    return t(getKey(namespace, key), ...(arg as I18nTranslationRestParameters));
  };

  return {
    ...methods,
    t: tFn,
  };
}
