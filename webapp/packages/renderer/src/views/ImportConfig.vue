<template>
  <div class="flex flex-col h-full px-5 py-10 relative">
    <a-button
      type="link"
      class="!absolute !left-9 !top-16"
      :onclick="goBack"
    >
      <arrow-left-outlined class="text-3xl text-primary" />
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
        <a-step class="">{{ t('import.step1') }}</a-step>
        <a-step>{{ t('import.step2') }}</a-step>
        <a-step>{{ t('import.step3') }}</a-step>
      </a-steps>
      <div class="w-fit h-full relative overflow-hidden alas-step-con-box">
        <div
          class="w-full h-full transition-all duration-500 ease-in-out absolute top-0 left-0"
          :style="transformStep1"
        >
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
            <template #upload-item="{fileItem}">
              <div :key="fileItem.key"></div>
            </template>
            <!--          <template #extra-button>-->
            <!--            <AButton type="primary">text</AButton>-->
            <!--          </template>-->
          </a-upload>
        </div>
        <div
          class="w-full h-full transition-all duration-500 ease-in-out absolute top-0 left-0 z-36"
          :style="transformStep2"
        >
          <a-typography-title :heading="3">{{ stepTipsOptions[current] }}</a-typography-title>
          <a-list>
            <a-list-item
              v-for="idx in 4"
              :key="idx"
            >
              <a-list-item-meta
                title="Beijing Bytedance Technology Co., Ltd."
                description="Beijing ByteDance Technology Co., Ltd. is an enterprise located in China."
              >
              </a-list-item-meta>
            </a-list-item>
          </a-list>
          <a-space class="mt-10 flex justify-end">
            <a-button :onclick="onCancel">取消</a-button>
            <a-button
              type="primary"
              :onclick="onOkSave"
            >
              确定
            </a-button>
          </a-space>
        </div>
        <div
          class="w-full h-full transition-all duration-500 ease-in-out absolute top-0 left-0 z-36"
          :style="transformStep3"
        >
          Success Icon
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {ref, unref, computed} from 'vue';
import AlasTitle from '/@/components/AlasTitle.vue';
import {ArrowLeftOutlined} from '@ant-design/icons-vue';
import router from '/@/router';
import {useI18n} from '/@/hooks/useI18n';

const {t} = useI18n();

const stepTipsOptions = ref({
  1: t('import.step1'),
  2: t('import.step2'),
  3: t('import.step3'),
});

const current = ref(1);

const transformStep1 = computed(
  () => {
    if (current.value === 1) return {transform: 'translateY(0)'};
    return {transform: 'translateY(-100%)'};
  },
  {
    onTrack: e => {
      console.log(e);
    },
  },
);
const transformStep2 = computed(() => {
  if (current.value === 1) return {transform: 'translateY(100%)'};
  if (current.value === 2) return {transform: 'translateY(0)'};
  return {transform: 'translateY(-100%)'};
});
const transformStep3 = computed(() => {
  if (current.value === 1) return {transform: 'translateY(100%)'};
  if (current.value === 2) return {transform: 'translateY(100%)'};
  return {transform: 'translateY(0)'};
});

const goBack = () => {
  router.back();
};

const customRequest = (option: {fileItem: any}) => {
  const {fileItem} = option;
  console.log(fileItem);
  current.value = 2;
  // TODO  保存一份文件的绝对路径
};

const onOkSave = () => {
  // TODO 复制一份文件到指定目录
  current.value = 3;
};

const onCancel = () => {
  // TODO 清除保存的文件信息
  current.value = 1;
};
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
  height: calc(100vh - 5rem);
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
