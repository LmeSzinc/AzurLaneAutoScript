<template>
  <div class="w-full h-full bg-white flex justify-center items-center">
    <AlasTitle />
  </div>
</template>

<script lang="ts">
import {defineComponent} from 'vue';
import AlasTitle from '/@/components/AlasTitle.vue';
export default defineComponent({
  name: 'InstallPage',
  components: {AlasTitle},
  setup() {
    return {};
  },
});
</script>

<style scoped></style>
