import type {LocaleSetting, LocaleType} from '/#/config';

export const LOCALE: { [key: string]: LocaleType } = {
    ZH_CN: 'zh_CN',
    EN_US: 'en-US',
    JA_JP: 'ja-JP',
    ZH_TW: 'zh-TW',
};

export const localeSetting: LocaleSetting = {
    showPicker: true,
    // Locale
    locale: LOCALE.ZH_CN,
    // Default locale
    fallback: LOCALE.ZH_CN,
    // available Locales
    availableLocales: [LOCALE.ZH_CN, LOCALE.EN_US, LOCALE.JA_JP, LOCALE.ZH_TW],
};

// locale list
export const localeList: { text: string; event: keyof typeof LOCALE }[] = [
    {
        text: '简体中文',
        event: LOCALE.ZH_CN,
    },
    {
        text: 'English',
        event: LOCALE.EN_US,
    },
    {
        text: 'English',
        event: LOCALE.JA_JP,
    },
    {
        text: 'English',
        event: LOCALE.ZH_TW,
    },
];
