<template>
<<<<<<< HEAD
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
=======
  <iframe class="alas" :src="url"></iframe>
</template>

<script lang="ts">
  import {defineComponent} from 'vue';
  import {webuiUrl} from '../../../main/src/config';

  export default defineComponent({
    name: 'Alas',
    computed: {
      url: function () {
        return webuiUrl;
      },
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
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
</style>
