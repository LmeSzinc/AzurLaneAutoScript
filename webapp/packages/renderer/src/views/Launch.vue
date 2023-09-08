<template>
  <div class="w-full h-full flex justify-center items-center flex-col relative">
    <section class="w-full flex items-center flex-col overflow-h">
      <LoadingOutlined class="text-6xl text-primary mb-20" />
      <AlasTitle />
      <div
        id="scrollRef"
        ref="scrollRef"
        class="w-10/12 max-w-156 h-96 mt-5 overflow-y-scroll overscroll-contain"
      >
        <main class="w-full max-w-full">
          <pre
            v-for="logInfo in logInfos"
            :key="logInfo"
            class="text-xs text-gray-400 w-full max-w-full whitespace-pre-wrap"
          >{{ logInfo }}</pre>
        </main>
      </div>
    </section>
    <ProgressBar
      class="absolute inset-x-0 bottom-0"
      :progress-value="progress"
    />
  </div>
</template>

<script lang="ts">
import {defineComponent, onMounted, ref, unref, nextTick} from 'vue';
import AlasTitle from '/@/components/AlasTitle.vue';
import ProgressBar from '/@/components/ProgressBar.vue';
import useIpcRenderer from '/@/hooks/useIpcRenderer';
import router from '../router';
import {LoadingOutlined} from '@ant-design/icons-vue';
import {ALAS_LOG, INSTALLER_READY, WINDOW_READY} from '@common/constant/eventNames';

export default defineComponent({
  name: 'LaunchPage',
  components: {
    AlasTitle,
    ProgressBar,
    LoadingOutlined,
  },
  setup() {
    const logInfos = ref<string[]>([]);
    const progress = ref<number>(0);
    const {ipcRendererOn, ipcRendererSend} = useIpcRenderer();
    const scrollRef = ref<HTMLElement>();

    onMounted(() => {
      ipcRendererSend(WINDOW_READY, true);

      ipcRendererOn(ALAS_LOG, async (_, arg: string) => {
        logInfos.value.push(arg);
        await nextTick();
        scrollToBottom();
        handelAlasInfo(arg);
        handleProgress(arg);
      });
    });

    const scrollToBottom = () => {
      const scrollDiv = unref(scrollRef);
      scrollDiv?.scrollTo(0, scrollDiv?.scrollHeight);
    };

    const handelAlasInfo = (logStr: string) => {
      if (logStr?.includes('Application startup complete') || logStr?.includes('bind on address')) {
        router.push('/alas')
      }
    };

    const handleProgress = (logStr: string) => {
      if (!logStr?.includes('Process')) return;
      const processInfo = logStr.match(/Process: \[\s(.+?)\s\]/g)?.pop();
      const processVal = processInfo?.match(/\d+/g)?.pop();
      processVal && (progress.value = Number(processVal));
      if (progress.value !== 100) return;
      ipcRendererSend(INSTALLER_READY, true);
    };

    return {
      logInfos,
      progress,
      scrollRef,
    };
  },
});
</script>

<style lang="less" scoped>
  #scrollRef::-webkit-scrollbar {
    width: 3px;
    height: 1px;
  }

  #scrollRef::-webkit-scrollbar-thumb {
    border-radius: 10px;
    background: #aeaeae;
  }

  #scrollRef::-webkit-scrollbar-track {
    border-radius: 10px;
    background: #ededed;
  }
</style>
