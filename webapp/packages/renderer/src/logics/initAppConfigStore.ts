import {useAppStore} from '/@/store/modules/app';
import {repositoryValueMap} from '/@/settings/repositorySeeing';

export async function initAppConfigStore() {
  const appStore = useAppStore();
  const config = await window.__electron_preload__getAlasConfig();
  appStore.setTheme(config?.theme ?? 'light');
  appStore.setLanguage(config?.language ?? 'zh-TW');
  appStore.setRepository(repositoryValueMap[config?.repository] ?? 'global');
}
