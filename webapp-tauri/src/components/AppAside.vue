<script setup lang="ts">
import { status } from '@/api/store'

defineProps<{
  active?: string
}>()

const emit = defineEmits<{
  select: [name: string]
}>()

function stateClass(state: number): string {
  if (state === 1) return 'aside-state-running'
  if (state === 3) return 'aside-state-warning'
  if (state === 4) return 'aside-state-updating'
  return ''
}
</script>

<template>
  <aside class="app-aside">
    <button
      class="btn btn-aside"
      :class="{ 'btn-aside-active': active === 'Home' }"
      @click="emit('select', 'Home')"
    >
      <span class="aside-icon icon-develop" />
      Home
    </button>
    <button
      v-for="inst in status.instances"
      :key="inst.name"
      class="btn btn-aside"
      :class="{ 'btn-aside-active': active === inst.name }"
      @click="emit('select', inst.name)"
    >
      <span class="aside-icon icon-run" />
      <span class="aside-state-dot" :class="stateClass(inst.state)" />
      {{ inst.name }}
    </button>
    <button
      class="btn btn-aside"
      :class="{ 'btn-aside-active': active === 'Manage' }"
      @click="emit('select', 'Manage')"
    >
      <span class="aside-icon icon-setting" />
      Manage
    </button>
  </aside>
</template>

<style scoped>
.app-aside {
  z-index: 91;
  padding-left: 0.125rem;
  padding-right: 0.325rem;
  padding-top: 1rem;
  overflow-y: auto;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}
.aside-icon {
  display: block;
  width: 2rem;
  height: 2rem;
  margin: 0 auto 2px;
  background-color: currentColor;
  -webkit-mask: no-repeat center / contain;
  mask: no-repeat center / contain;
}
.icon-develop {
  -webkit-mask-image: url('/icon/develop.svg');
  mask-image: url('/icon/develop.svg');
}
.icon-run {
  -webkit-mask-image: url('/icon/run.svg');
  mask-image: url('/icon/run.svg');
}
.icon-setting {
  -webkit-mask-image: url('/icon/setting.svg');
  mask-image: url('/icon/setting.svg');
}
.aside-state-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 3px;
  background: #8a939c;
}
.aside-state-running {
  background: #4cd07d;
}
.aside-state-warning {
  background: #e6a23c;
}
.aside-state-updating {
  background: #4c9aff;
}
</style>
