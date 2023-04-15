<template>
  <div class="w-full h-full flex justify-center items-center flex-col relative">
    <section class="w-full flex items-center flex-col overflow-h">
      <LoadingOutlined class="text-6xl text-primary mb-20" />
      <AlasTitle />
      <div
        id="scrollRef"
        ref="scrollRef"
        class="w-10/12 max-w-3xl h-96 overflow-y-scroll overscroll-contain"
      >
        <main class="w-full max-w-full">
          <section
            v-for="logInfo in logInfos"
            :key="logInfo"
            class="text-sm text-gray-400 leading-4"
          >
            <pre class="w-full max-w-full whitespace-pre-wrap">
              {{ logInfo }}
         </pre>
          </section>
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
        const ipcRenderer = useIpcRenderer();
        const ipcRendererIns = ipcRenderer.value;
        const scrollRef = ref<HTMLElement>();

        onMounted(() => {
            ipcRendererIns.send('window-ready', true);

            ipcRendererIns.on('alas-log', async (_: never, arg: string) => {
                logInfos.value.push(arg);
                await nextTick();
                scrollToBottom();
                if (!arg.includes('Process')) return;
                const processInfo = arg.match(/Process: \[\s(.+?)\s\]/g)?.pop();
                const processVal = processInfo?.match(/\d+/g)?.pop();
                processVal && (progress.value = Number(processVal));
                if (progress.value !== 100) return;
                setTimeout(() => {
                    router.push('/alas');
                }, 1000);

            });
        });

        const scrollToBottom = () => {
            const scrollDiv = unref(scrollRef);
            scrollDiv?.scrollTo(0, scrollDiv?.scrollHeight);
        };


        return {
            logInfos,
            progress,
            scrollRef,
        };
    },
});
</script>
