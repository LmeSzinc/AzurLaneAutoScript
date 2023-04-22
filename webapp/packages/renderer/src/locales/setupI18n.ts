import type {I18n, I18nOptions} from 'vue-i18n';
import {createI18n} from 'vue-i18n';
import type {App} from 'vue';
import {LOCALE, localeSetting} from '/@/settings/localSetting';
// import {setHtmlPageLang, setLoadLocalePool} from '/@/locales/helper';
import {useAppStore} from '/@/store/modules/app';
import {LocaleMap} from '/@/locales/localeMap';
import {unref} from 'vue';

export let i18n: ReturnType<typeof createI18n>;

const {fallback, availableLocales} = localeSetting;

async function createI18nOptions(): Promise<I18nOptions> {
  const appStore = useAppStore();
  const locale = unref(appStore.getLanguage) || 'en-US';
  console.log('createI18nOptions', locale);
  // setHtmlPageLang(locale);
  // setLoadLocalePool(loadLocalePool => {
  //   loadLocalePool.push(locale);
  // });

  return {
    legacy: false,
    locale,
    fallbackLocale: fallback,
    messages: {
      [LOCALE.ZH_CN]: LocaleMap[LOCALE.ZH_CN].message,
      [LOCALE.EN_US]: LocaleMap[LOCALE.EN_US].message,
      [LOCALE.JA_JP]: LocaleMap[LOCALE.JA_JP].message,
      [LOCALE.ZH_TW]: LocaleMap[LOCALE.ZH_TW].message,
    },
    availableLocales: availableLocales,
    sync: false, //If you don’t want to inherit locale from global scope, you need to set sync of i18n component option to false.
    silentTranslationWarn: true, // true - warning off
    missingWarn: false,
    silentFallbackWarn: true,
  };
}

// setup i18n instance with glob
export async function setupI18n(app: App) {
  const options = await createI18nOptions();
  console.log({options});
  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  // @ts-ignore
  i18n = createI18n(options) as I18n;
  app.use(i18n);
}
