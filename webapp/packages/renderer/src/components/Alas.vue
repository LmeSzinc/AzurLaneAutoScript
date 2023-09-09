<template>
  <iframe
    class="alas"
    :src="webuiUrl"
  ></iframe>
</template>

<script lang="ts">
import {computed, defineComponent} from 'vue';
import {useAppStoreWithOut} from '/@/store/modules/app';

export default defineComponent({
  name: 'AlasPage',
  setup() {
    const appStore = useAppStoreWithOut();
    const webuiUrl = computed(() => appStore.webuiUrl);
    return {
      webuiUrl,
    };
  },
});
</script>

<style scoped>
.alas {
  border-width: 0;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}
</style>
