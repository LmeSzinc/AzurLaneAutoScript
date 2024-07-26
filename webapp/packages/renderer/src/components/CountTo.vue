<template>
  <span
    :class="{prefixClass}"
    :style="{color}"
  >
    {{ value }}
  </span>
</template>

<script lang="ts">
import type {PropType} from 'vue';
import {defineComponent, ref, watchEffect, computed, unref, watch, onMounted} from 'vue';
import {useTransition, TransitionPresets} from '@vueuse/core';
import {isNumber} from '/@/utils/is';
export default defineComponent({
  name: 'CountTo',
  props: {
    startVal: {type: Number, default: 0},
    endVal: {type: Number, default: 100},
    duration: {type: Number, default: 1500},
    autoplay: {type: Boolean, default: false},
    decimals: {
      type: Number,
      default: 0,
      validator(value: number) {
        return value >= 0;
      },
    },
    prefix: {type: String, default: ''},
    suffix: {type: String, default: ''},
    separator: {type: String, default: ','},
    decimal: {type: String, default: '.'},
    prefixClass: {type: String, default: ''},
    color: {type: String},
    useEasing: {type: Boolean, default: true},
    transition: {type: String as PropType<keyof typeof TransitionPresets>, default: 'linear'},
  },
  emits: ['onStarted', 'onFinished'],
  setup(props, {emit}) {
    const source = ref(props.startVal);
    const disabled = ref(false);
    let outputValue = useTransition(source);
    const value = computed(() => formatNumber(unref(outputValue)));

    watchEffect(() => {
      source.value = props.startVal;
    });

    function formatNumber(num: number | string) {
      if (!num && num !== 0) {
        return '';
      }
      const {decimals, decimal, separator, suffix, prefix} = props;
      num = Number(num).toFixed(decimals);
      num += '';

      const x = num.split('.');
      let x1 = x[0];
      const x2 = x.length > 1 ? decimal + x[1] : '';

      const rgx = /(\d+)(\d{3})/;
      if (separator && !isNumber(separator)) {
        while (rgx.test(x1)) {
          x1 = x1.replace(rgx, '$1' + separator + '$2');
        }
      }
      return prefix + x1 + x2 + suffix;
    }

    watch([() => props.startVal, () => props.endVal], () => {
      if (props.autoplay) {
        start();
      }
    });

    onMounted(() => {
      props.autoplay && start();
    });

    function start() {
      run();
      source.value = props.endVal;
    }

    function reset() {
      source.value = props.startVal;
      run();
    }

    function run() {
      outputValue = useTransition(source, {
        disabled,
        duration: props.duration,
        onFinished: () => emit('onFinished'),
        onStarted: () => emit('onStarted'),
        ...(props.useEasing ? {transition: TransitionPresets[props.transition]} : {}),
      });
    }

    return {
      value,
      start,
      reset,
    };
  },
});
</script>

<style scoped></style>
