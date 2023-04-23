<template>
  <div class="flex flex-col h-full px-5 py-10 relative">
    <a-button
      type="link"
      class="absolute left-9 top-16"
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
      <div class="w-fit h-full">
        <a-typography-title :heading="3">{{ stepTipsOptions[current] }}</a-typography-title>
        <a-upload
          class=""
          draggable
          action="/"
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
        </a-upload>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {ref} from 'vue';
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

const goBack = () => {
  router.back();
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
        background: #f0f0f0;
        color: rgb(var(--primary-6));
      }
    }
  }
}
[arco-theme='light'] {
  .alas-upload {
    border: 2px solid #f0f0f0;
  }
  :deep(.arco-steps-item-wait) {
    .arco-steps-item-node {
      .arco-steps-icon {
        background: white;
      }
    }
  }
}

[arco-theme='dark'] {
  .alas-upload {
    border: 2px solid rgba(240, 240, 240, 0.53);
  }
  :deep(.arco-steps-item-wait) {
    .arco-steps-item-node {
      .arco-steps-icon {
        background: #f0f0f0;
      }
    }
  }
}

.alas-upload {
  border: 2px solid rgba(240, 240, 240, 0.53);
  border-radius: 2.5rem;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  width: calc(100vw - 32rem);
  height: calc(100vh - 22rem);
  max-width: 789px;
  max-height: 485px;
}
</style>
