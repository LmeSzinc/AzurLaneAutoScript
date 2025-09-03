<template>
  <div id="app">
    <app-header></app-header>
    <router-view></router-view>
  </div>
</template>

<script lang="ts">
  import {defineComponent} from 'vue';
  import AppHeader from '/@/components/AppHeader.vue'

  export default defineComponent({
    name: 'App',
    components: {
      AppHeader
    },
  });
</script>

<style>
  #app {
    width: 100vw;
    height: 100vh;
    overflow: hidden;
  }

  body {
    margin: 0;
    padding: 0;
  }
</style>
