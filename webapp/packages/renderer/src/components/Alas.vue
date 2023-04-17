<template>
  <iframe
    class="alas"
    :src="alasConfig.webuiUrl"
  ></iframe>
</template>

<script lang="ts">
import {defineComponent} from 'vue';
import useAlasConfig from '/@/hooks/useAlasConfig';

export default defineComponent({
    name: 'AlasPage',
    setup() {
        const alasConfig = useAlasConfig();
        return {
            alasConfig,
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
