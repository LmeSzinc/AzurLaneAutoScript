/**
 * Multi-language related operations
 */
import type {LocaleType} from '/#/config';
import {i18n} from './setupI18n';
import {useLocaleStoreWithOut} from '/@/store/modules/locale';
import {unref, computed} from 'vue';
import messages from '@intlify/unplugin-vue-i18n/messages';

function setI18nLanguage(locale: LocaleType) {
  const localeStore = useLocaleStoreWithOut();
  if (i18n.mode === 'legacy') {
    i18n.global.locale = locale;
  } else {
    (i18n.global.locale as any).value = locale;
  }
  localeStore.setLocaleInfo({locale});
}

export function useLocale() {
  const localeStore = useLocaleStoreWithOut();
  const getLocale = computed(() => localeStore.getLocale);

  const getArcoLocale = computed((): any => {
    return i18n.global.getLocaleMessage(unref(getLocale)) ?? {};
  });

  // Switching the language will change the locale of useI18n
  // And submit to configuration modification
  async function changeLocale(locale: LocaleType) {
    const globalI18n = i18n.global;
    const currentLocale = unref(globalI18n.locale);
    if (currentLocale === locale) {
      return locale;
    }
    const langModule = messages[locale];
    if (!langModule) return;

    globalI18n.setLocaleMessage(locale, langModule);

    setI18nLanguage(locale);
    return locale;
  }

  return {
    getLocale,
    changeLocale,
    getArcoLocale,
  };
}
