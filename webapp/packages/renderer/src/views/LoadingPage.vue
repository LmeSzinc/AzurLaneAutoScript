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
import router from '/@/router';
onMounted(() => {
  const isFirst = window.__electron_preload__checkIsNeedInstall();
  setTimeout(() => {
    if (!isFirst) {
      router.push('/Install');
    } else {
      router.push('/Lunch');
    }
  }, 1000);
  // if (!isFirst) {
  //   router.push('/Install');
  // } else {
  //   router.push('/Lunch');
  // }
});
</script>

<style scoped></style>
