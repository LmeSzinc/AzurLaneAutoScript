<template>
  <div class="app-header">
    <div class="header-drag"></div>
    <div class="header-icon">
      <MinusOutlined class="icon" @click="minimizeWin"></MinusOutlined>
      <BorderOutlined class="icon" @click="maximizeWin"></BorderOutlined>
      <CloseOutlined class="icon" @click="closeWin"></CloseOutlined>
    </div>
  </div>
</template>

<script lang="ts">
  import {defineComponent} from 'vue';
  import {BorderOutlined, CloseOutlined, MinusOutlined} from '@ant-design/icons-vue';

  const ipcRenderer = require('electron').ipcRenderer;

  export default defineComponent({
    name: 'AppHeader',
    components: {
      MinusOutlined,
      BorderOutlined,
      CloseOutlined,
    },
    methods: {
      minimizeWin() {
        ipcRenderer.send('window-min');
      },
      maximizeWin() {
        ipcRenderer.send('window-max');
      },
      closeWin() {
        ipcRenderer.send('window-close');
      },
    },
  });
</script>

<style scoped>
  .app-header {
    position: fixed;
    left: 0;
    top: 0;
    width: 100%;
    height: 60px;
    display: flex;
    flex-direction: row;
    -webkit-app-region: drag;
  }

  .header-drag {
    width: 100%;
    height: 100%;
  }

  .header-icon {
    -webkit-app-region: no-drag;
    text-align: right;
    font-size: 20px;
    color: #7c7c7c;
    display: flex;
    align-items: center;
  }

  .icon {
    padding: 10px;
    margin-right: 5px;
  }
</style>
