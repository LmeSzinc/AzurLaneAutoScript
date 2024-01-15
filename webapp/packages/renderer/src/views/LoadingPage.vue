<template>
  <div class="w-full h-full flex justify-center items-center">
    <ASpin
      dot
      :size="30"
      tip="Alas Loading..."
    />
  </div>
</template>

<script lang="ts" setup>
import {onMounted} from 'vue';
import router from '@/router';
import {dispatch} from '@/utils';
onMounted(async () => {
  const isFirst = await dispatch('/system/is-first-open');
  if (!isFirst) {
    await router.push('/Install');
  } else {
    await router.push('/Launch');
  }
});
</script>

<style scoped></style>
