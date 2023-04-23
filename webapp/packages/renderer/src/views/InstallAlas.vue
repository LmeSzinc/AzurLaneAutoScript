<template>
  <div class="w-full h-full flex justify-center items-center flex-col">
    <AlasTitle />
    <section class="mt-5">
      <a-form
        class="alas-install"
        layout="inline"
        :label-col="{style: 'width: 100px'}"
        :label-align="'left'"
        :model="configForm"
      >
        <a-form-item
          :wrapper-col="{style: 'width: 100%'}"
          :label="t('common.language')"
          name="language"
        >
          <a-select
            v-model="configForm.language"
            :options="localeList"
            @change="selectLanguage"
          />
        </a-form-item>
        <a-form-item
          :wrapper-col="{span: 16}"
          :label="t('common.update')"
          name="repository"
        >
          <a-select
            v-model="configForm.repository"
            :options="repositoryOptions"
            @change="selectRepository"
          />
        </a-form-item>
        <a-form-item
          :wrapper-col="{span: 16}"
          :label="t('common.theme')"
          name="theme"
        >
          <a-select
            v-model="configForm.theme"
            :options="themeOptions"
            @change="selectTheme"
          />
        </a-form-item>
      </a-form>
      <div class="w-full text-end">
        <a-button
          type="link"
          class="text-end mt-5 cursor-pointer"
          :onclick="goToImportPage"
        >
          <span class="text-slate dark:text-white">{{ t('common.installTips') }}</span>
        </a-button>
      </div>
    </section>
    <a-Button
      type="primary"
      size="large"
      class="mt-16 w-32"
    >
      <span class="text-current">{{ t('common.install') }}</span>
    </a-Button>
  </div>
</template>

<script lang="ts" setup>
import AlasTitle from '/@/components/AlasTitle.vue';
import {useI18n} from '/@/hooks/useI18n';
import {computed, ref, unref} from 'vue';
import {localeList} from '/@/settings/localSetting';
import {useAppStoreWithOut} from '/@/store/modules/app';
import type {LocaleType} from '/#/config';
import {setupThemeSetting} from '/@/settings/themeSetting';
import {useLocale} from '/@/locales/useLocale';
import router from '/@/router';

const {t} = useI18n();
const appStore = useAppStoreWithOut();
const {changeLocale} = useLocale();

const configForm = ref<{
  language: LocaleType;
  repository: string;
  theme: AlasConfig['theme'];
}>({
  language: unref(appStore.getLanguage),
  repository: unref(appStore.getRepository),
  theme: unref(appStore.theme),
});

const repositoryOptions = computed(() => [
  {
    label: t('common.global'),
    value: 'global',
  },
  {
    label: t('common.china'),
    value: 'china',
  },
]);

const themeOptions = computed(() => [
  {
    label: t('common.light'),
    value: 'light',
  },
  {
    label: t('common.dark'),
    value: 'dark',
  },
]);

const selectLanguage = (value: LocaleType) => {
  appStore.setLanguage(value);
  changeLocale(value);
};
const selectRepository = (value: string) => {
  appStore.setRepository(value);
};
const selectTheme = (value: AlasConfig['theme']) => {
  appStore.setTheme(value);
  setupThemeSetting(value);
};

const goToImportPage = () => {
  router.push('/import');
};
</script>

<style scoped></style>
