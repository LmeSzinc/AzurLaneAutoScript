<template>
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
</style>
