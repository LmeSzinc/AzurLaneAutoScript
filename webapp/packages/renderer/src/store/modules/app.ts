import {defineStore} from 'pinia';
import {store} from '/@/store';
import type {LocaleType, ThemeVal} from '/#/config';

export const useAppStore = defineStore({
  id: 'app',
  state: (): AlasConfig => ({
    theme: 'light',
    language: 'zh-CN',
    repository: '',
    webuiUrl: '',
  }),
  getters: {
    getTheme(): string {
      return this.theme;
    },
    getLanguage(): LocaleType {
      return this.language;
    },
    getRepository(): string {
      return this.repository;
    },
    getWebuiUrl(): string {
      return this.webuiUrl;
    },
  },
  actions: {
    setTheme(theme: ThemeVal) {
      this.theme = theme;
    },
    setLanguage(language: LocaleType) {
      this.language = language;
    },
    setRepository(repository: AlasConfig['repository']) {
      this.repository = repository;
    },
    setWebuiUrl(webuiUrl: AlasConfig['webuiUrl']) {
      this.webuiUrl = webuiUrl;
    },
  },
});

export function useAppStoreWithOut() {
  return useAppStore(store);
}
