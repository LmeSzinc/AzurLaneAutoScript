<template>
  <div class="flex flex-col h-full px-5 py-10 relative">
    <a-button
      type="text"
      class="absolute left-9 top-16"
      :onclick="goBack"
    >
      <arrow-left-outlined class="text-3xl" />
    </a-button>
    <AlasTitle class="ml-20 mt-2" />
    <a-steps
      :current="current"
      direction="vertical"
      class="mt-5 ml-48"
    >
      <a-step class="">选择旧的Alas</a-step>
      <a-step>确认配置文件</a-step>
      <a-step>导入完成</a-step>
    </a-steps>
  </div>
</template>

<script lang="ts">
import {defineComponent, ref} from 'vue';
import AlasTitle from '/@/components/AlasTitle.vue';
import {ArrowLeftOutlined} from '@ant-design/icons-vue';
import router from '/@/router';
export default defineComponent({
  name: 'ImportConfig',
  components: {
    AlasTitle,
    ArrowLeftOutlined,
  },
  setup() {
    const current = ref(1);

    const goBack = () => {
      router.back();
    };

    return {current, goBack};
  },
});
</script>

<style scoped></style>
