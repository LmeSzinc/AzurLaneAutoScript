import {useAppStore} from '@/store/modules/app';
import {repositoryValueMap} from '@/settings/repositorySeeing';
import {dispatch} from '@/utils';

export async function initAppConfigStore() {
  const appStore = useAppStore();
  // const config = await window.__electron_preload__getAlasConfig();
  const config = await dispatch('/system/get-alas-config');
  appStore.setTheme(config?.theme ?? 'light');
  appStore.setLanguage(config?.language ?? 'zh-TW');
  appStore.setRepository(
    (repositoryValueMap[config?.repository] as 'global' | 'china') ?? 'global',
  );
  appStore.setWebuiUrl(config?.webuiUrl ?? '127.0.0.1:22267');
  appStore.setAlasPath(config?.alasPath ?? '');
}
