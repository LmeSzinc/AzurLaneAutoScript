<template>
  <section class="w-full">
    <span class="text-primary flex text-2xl ml-5 mb-3">{{ progressValue }}%</span>
    <div
      class="h-3 bg-primary ease-in-out duration-500"
      :style="getWrapStyle"
    ></div>
  </section>
</template>

<script lang="ts" setup>
import {propTypes} from '/@/utils/propTypes';
import type {CSSProperties} from 'vue';
import {computed, unref} from 'vue';

const props = defineProps({
  progressValue: propTypes.number.def(0),
});

const getWrapStyle = computed((): CSSProperties => {
  return {
    width: `${unref(isNaN(props.progressValue) ? 0 : props.progressValue)}%`,
  };
});
</script>

<style scoped></style>
