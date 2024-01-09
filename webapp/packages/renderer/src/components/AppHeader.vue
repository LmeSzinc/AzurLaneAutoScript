<template>
  <div class="app-header">
    <div class="header-drag"></div>
    <div class="header-icon">
      <ArrowDownOutlined
        class="icon"
        @click="trayWin"
      ></ArrowDownOutlined>
      <MinusOutlined
        class="icon"
        @click="minimizeWin"
      ></MinusOutlined>
      <BorderOutlined
        class="icon"
        @click="maximizeWin"
      ></BorderOutlined>
      <CloseOutlined
        class="icon"
        @click="closeWin"
      ></CloseOutlined>
    </div>
  </div>
</template>

<script lang="ts">
import {defineComponent, h} from 'vue';
import {
  BorderOutlined,
  CloseOutlined,
  MinusOutlined,
  ArrowDownOutlined,
} from '@ant-design/icons-vue';
import {Modal} from '@arco-design/web-vue';
import {useI18n} from '@/hooks/useI18n';
import {dispatch} from '@/utils';

export default defineComponent({
  name: 'AppHeader',
  components: {
    ArrowDownOutlined,
    MinusOutlined,
    BorderOutlined,
    CloseOutlined,
  },
  setup() {
    const {t} = useI18n();

    const trayWin = () => {
      dispatch('/browser/window-tray');
    };
    const minimizeWin = () => {
      dispatch('/browser/minimize-current');
    };
    const maximizeWin = () => {
      dispatch('/browser/maximize-current');
    };
    const closeWin = () => {
      Modal.confirm({
        title: () =>
          h(
            'div',
            {
              class: 'flex justify-center items-center font-bold',
            },
            t('modal.closeTipTitle'),
          ),
        content: () =>
          h(
            'div',
            {
              class: 'flex justify-center items-center',
            },
            t('modal.closeTipContent'),
          ),
        cancelText: t('modal.cancelText'),
        okText: t('modal.okText'),
        titleAlign: 'center',
        okButtonProps: {
          size: 'medium',
        },
        onOk() {
          // ipcRendererSend('window-close');
          dispatch('/browser/close-current');
        },
      });
    };
    return {
      trayWin,
      minimizeWin,
      maximizeWin,
      closeWin,
    };
  },
});
</script>

<style scoped>
.app-header {
  position: fixed;
  left: 0;
  top: 0;
  width: 100%;
  height: 51px;
  display: flex;
  flex-direction: row;
  -webkit-app-region: drag;
  z-index: 999;
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
