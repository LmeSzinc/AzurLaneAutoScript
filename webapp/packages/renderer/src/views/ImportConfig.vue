<template>
  <div class="flex flex-col h-full px-5 py-10 relative">
    <a-button
      type="text"
      class="!absolute !left-9 !top-18 !hover:bg-white"
      :onclick="goBack"
    >
      <arrow-left-outlined class="text-3xl text-slate opacity-25" />
    </a-button>
    <section class="ml-20 mt-2">
      <AlasTitle />
      <span>{{ t('import.title') }}</span>
    </section>
    <div class="flex">
      <a-steps
        :current="current"
        direction="vertical"
        class="mt-5 ml-64 w-32 alas-steps h-64"
      >
        <a-step>
          {{ t('import.step1') }}
          <template #icon> 1</template>
        </a-step>
        <a-step>
          {{ t('import.step2') }}
          <template #icon> 2</template>
        </a-step>
        <a-step>
          {{ t('import.step3') }}
          <template #icon> 3</template>
        </a-step>
      </a-steps>
      <div class="w-fit h-full relative overflow-hidden alas-step-con-box">
        <div
          class="w-full h-full transition-all duration-500 ease-in-out absolute top-0 left-0 flex flex-col justify-between"
          :style="transformStep1"
        >
          <div>
            <a-typography-title :heading="3">{{ stepTipsOptions[current] }}</a-typography-title>
            <a-upload
              draggable
              multiple
              :custom-request="customRequest"
              accept=".json,.yaml"
            >
              <template #upload-button>
                <div class="alas-upload">
                  <div>
                    <a-typography-title
                      :heading="4"
                      class="opacity-25"
                    >
                      {{ t('import.file.choose') }}
                    </a-typography-title>
                  </div>
                </div>
              </template>
              <template #upload-item></template>
            </a-upload>
          </div>
        </div>
        <div
          class="w-full h-full transition-all duration-500 ease-in-out absolute top-0 left-0 z-36 flex flex-col justify-between"
          :style="transformStep2"
        >
          <div>
            <a-typography-title :heading="3">{{ stepTipsOptions[current] }}</a-typography-title>
            <a-typography-text ellipsis>
              {{ fileParentPath }}{{ t('import.filePathTips') }}
            </a-typography-text>
            <section class="flex justify-between w-full">
              <a-typography-title :heading="6">{{ t('import.fileName') }}</a-typography-title>
              <a-typography-title :heading="6">{{ t('import.lastModify') }}</a-typography-title>
            </section>
            <a-list>
              <a-list-item
                v-for="fileItem in fileItems"
                :key="fileItem.uid"
              >
                <a-list-item-meta :title="fileItem.name"></a-list-item-meta>
                <template #actions>
                  <span>{{ fileItem.lastModifyTime }}</span>
                </template>
              </a-list-item>
            </a-list>
          </div>

          <a-space class="mt-10 flex justify-end">
            <a-button
              :onclick="onCancel"
              size="large"
            >
              {{ t('import.btnGoBack') }}
            </a-button>
            <a-button
              type="primary"
              :onclick="onOkSave"
              size="large"
              :loading="saveLoading"
            >
              {{ t('import.btnImport') }}
            </a-button>
          </a-space>
        </div>
        <div
          class="w-full h-full transition-all duration-500 ease-in-out absolute top-0 left-0 z-36 flex flex-col justify-between"
          :style="transformStep3"
        >
          <div>
            <a-typography-title :heading="3">{{ stepTipsOptions[current] }}</a-typography-title>
            <section class="flex justify-start">
              <a-typography-text
                :ellipsis="{
                  rows: 1,
                  showTooltip: true,
                  css: true,
                }"
              >
                {{ fileParentPath }}
              </a-typography-text>
              <a-typography-text class="min-w-[250px]">
                {{ t('import.filePathTips') }}
              </a-typography-text>
            </section>
            <section class="flex justify-between w-full">
              <a-typography-title :heading="6">{{ t('import.fileName') }}</a-typography-title>
              <a-typography-title :heading="6">{{ t('import.lastModify') }}</a-typography-title>
            </section>
            <a-list>
              <a-list-item
                v-for="fileItem in fileItems"
                :key="fileItem.uid"
              >
                <a-list-item-meta :title="fileItem.name"></a-list-item-meta>
                <template #actions>
                  <span>{{ fileItem.lastModifyTime }}</span>
                </template>
              </a-list-item>
            </a-list>
          </div>
          <a-space class="mt-10 flex justify-end">
            <a-button
              :onclick="onReimport"
              size="large"
            >
              {{ t('import.btnReimport') }}
            </a-button>
            <a-button
              type="primary"
              :onclick="goBack"
              size="large"
            >
              {{ t('import.btnOk') }}
            </a-button>
          </a-space>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {computed, ref} from 'vue';
import AlasTitle from '/@/components/AlasTitle.vue';
import {ArrowLeftOutlined} from '@ant-design/icons-vue';
import router from '/@/router';
import {useI18n} from '/@/hooks/useI18n';
import dayjs from 'dayjs';
import {useAppStore} from '/@/store/modules/app';
import {Modal} from '@arco-design/web-vue';
import type {RequestOption} from '@arco-design/web-vue/es/upload/interfaces';

const {t} = useI18n();

const stepTipsOptions = ref({
  1: t('import.step1'),
  2: t('import.step2'),
  3: t('import.step3'),
});

const appStore = useAppStore();

const saveLoading = ref<boolean>(false);

const fileItems = ref<
  {file: File | undefined; uid: string; name: string; lastModifyTime: string}[]
>([]);

const current = ref(1);

const fileParentPath = computed(() => {
  let pathStr = '';
  fileItems.value.forEach(item => {
    const [path] = item?.file?.path.split('AzurLaneAutoScript') || ['unknown'];
    if (pathStr !== path) pathStr = path;
  });
  return pathStr + 'AzurLaneAutoScript';
});

const transformStep1 = computed(() => {
  if (current.value === 1) return {transform: 'translateY(0)'};
  return {transform: 'translateY(-100%)', opacity: 0};
});
const transformStep2 = computed(() => {
  if (current.value === 1) return {transform: 'translateY(100%)', opacity: 0};
  if (current.value === 2) return {transform: 'translateY(0)'};
  return {transform: 'translateY(-100%)', opacity: 0};
});
const transformStep3 = computed(() => {
  if (current.value === 3) return {transform: 'translateY(0)'};
  return {transform: 'translateY(100%)', opacity: 0};
});

const goBack = () => {
  router.back();
};

const customRequest = (option: RequestOption) => {
  const {fileItem} = option;
  current.value = 2;
  fileItems.value.push({
    file: fileItem.file,
    uid: fileItem.uid,
    name: fileItem?.file?.name || '',
    lastModifyTime: dayjs(fileItem?.file?.lastModified || new Date()).format('YYYY-MM-DD HH:mm:ss'),
  });
};

const onOkSave = async () => {
  saveLoading.value = true;
  const paths = fileItems.value.map(item => item.file.path);
  // TODO 复制一份文件到指定目录
  await window.__electron_preload__copyFilesToDir(paths, appStore.getAlasPath + '/config', {
    filedCallback: e => {
      Modal.error({
        title: 'Error Notification',
        content: e.toString(),
      });
    },
  });

  saveLoading.value = false;

  current.value = 3;
};

const onCancel = () => {
  current.value = 1;
  fileItems.value = [];
};

const onReimport = onCancel;
</script>

<style lang="less" scoped>
.alas-steps {
  :deep(.arco-steps-item) {
    overflow: visible;
    width: 100px;
  }

  :deep(.arco-steps-item-content) {
    width: 200px;
    text-align: right;
    transform: translateX(-250px);
  }

  :deep(.arco-steps-item-wait) {
    .arco-steps-item-node {
      .arco-steps-icon {
        border: 2px solid rgb(var(--primary-6));
        color: rgb(var(--primary-6));
      }
    }
  }
}

.alas-step-con-box {
  width: calc(100vw - 32rem);
  height: calc(100vh - 15rem);
}

.alas-upload {
  border-radius: 2rem;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  width: calc(100vw - 32rem);
  height: calc(100vh - 22rem);
  max-width: 789px;
  max-height: 485px;
}

body[arco-theme='light'] {
  .alas-upload {
    border: 2px solid var(--color-border-1);
  }

  .alas-steps {
    :deep(.arco-steps-item-wait) {
      .arco-steps-item-node {
        .arco-steps-icon {
          background: var(--color-bg-4);
        }
      }
    }
  }
}

body[arco-theme='dark'] {
  .alas-upload {
    border: 2px solid var(--color-border-3);
  }

  .alas-steps {
    :deep(.arco-steps-item-wait) {
      .arco-steps-item-node {
        .arco-steps-icon {
          background: var(--color-bg-4);
        }
      }
    }
  }
}
</style>
