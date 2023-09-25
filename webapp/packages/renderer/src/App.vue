<template>
  <a-config-provider :locale="locale">
    <div
      id="app"
      class="bg-white dark:bg-dark text-slate dark:text-neutral"
    >
      <app-header></app-header>
      <router-view>
        <template #default="{Component, route}">
          <transition
            name="fade-slide"
            mode="out-in"
            appear
          >
            <component
              :is="Component"
              :key="route.fullPath"
            />
          </transition>
        </template>
      </router-view>
    </div>
  </a-config-provider>
</template>

<script lang="ts">
import {computed, defineComponent, unref} from 'vue';
import AppHeader from '/@/components/AppHeader.vue';
import {useLocale} from '/@/locales/useLocale';
import {setTheme} from '/@/settings/themeSetting';
import {useAppStoreWithOut} from '/@/store/modules/app';
import zhCN from '@arco-design/web-vue/es/locale/lang/zh-cn';
import enUS from '@arco-design/web-vue/es/locale/lang/en-us';
import jaJP from '@arco-design/web-vue/es/locale/lang/ja-jp';
import zhTW from '@arco-design/web-vue/es/locale/lang/zh-tw';
import type {ArcoLang} from '@arco-design/web-vue/es/locale/interface';

export default defineComponent({
  name: 'App',
  components: {
    AppHeader,
  },
  setup() {
    const {getLocale} = useLocale();
    const locales = {
      'zh-CN': zhCN,
      'en-US': enUS,
      'ja-JP': jaJP,
      'zh-TW': zhTW,
    };

    const locale = computed<ArcoLang>(() => {
      const language = unref(getLocale);
      return locales[language];
    });
    const appStore = useAppStoreWithOut();
    setTheme(appStore.theme);
    return {
      locale,
    };
  },
});
</script>

<style>
#app {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}

body {
  margin: 0;
  padding: 0;
}

.fade-slide-leave-active,
.fade-slide-enter-active {
  transition: all 0.3s;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>
