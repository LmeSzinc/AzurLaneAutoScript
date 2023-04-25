<template>
  <section class="w-full">
    <CountTo
      :class="'text-primary flex text-2xl ml-5 mb-3'"
      :start-val="progressValue"
      suffix="%"
    /><div
      class="h-3 bg-primary ease-in-out duration-500"
      :style="getWrapStyle"
    ></div>
  </section>
</template>

<script lang="ts" setup>
import VueTypes from 'vue-types';
import type {CSSProperties} from 'vue';
import {computed, unref} from 'vue';
import CountTo from './CountTo.vue';

const props = defineProps({
  progressValue: VueTypes.number.def(0),
});

const getWrapStyle = computed((): CSSProperties => {
  return {
    width: `${unref(isNaN(props.progressValue) ? 0 : props.progressValue)}%`,
  };
});
</script>

<style scoped></style>
