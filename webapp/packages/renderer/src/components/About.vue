<template>
  <h2 id="versions">
    Lib versions
  </h2>
  <div>
    <ul aria-labelledby="versions">
      <li
        v-for="(version, lib) in versions"
        :key="lib"
      >
        <strong>{{ lib }}</strong>: v{{ version }}
      </li>
    </ul>
  </div>
</template>

<script lang="ts">
import {defineComponent} from 'vue';
import {useElectron} from '/@/use/electron';
export default defineComponent({
  name: 'App',
  setup() {
    const {versions} = useElectron();
    // It makes no sense to make "versions" reactive
    return {versions};
  },
});
</script>

<style scoped>
div {
  text-align: left;
  display: grid;
  justify-content: center;
}
</style>
