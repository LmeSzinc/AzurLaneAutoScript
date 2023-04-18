import {defineStore} from 'pinia';
import type {DefSetting, LocaleType} from '/#/config';
import {defSetting} from '/@/setting';
import {store} from '/@/store';

interface SettingState {
  settingInfo: DefSetting;
}

export const useSettingStore = defineStore({
  id: 'app-setting',
  state: (): SettingState => ({
    settingInfo: defSetting,
  }),
  getters: {
    getLocale(): LocaleType {
      return this.settingInfo?.locale ?? 'zh_CN';
    },
  },
  actions: {
    /**
     * Set up multilingual information and cache
     * @param info multilingual info
     */
    setSettingInfo(info: Partial<DefSetting>) {
      this.settingInfo = {...this.settingInfo, ...info};
      // Set language to yaml file
    },
    /**
     * Initialize multilingual information and load the existing configuration from the local cache
     */
    initLocale() {
      this.setSettingInfo({
        ...defSetting,
        ...this.settingInfo,
      });
    },
  },
});

export function useSettingStoreWithOut() {
  return useSettingStore(store);
}
