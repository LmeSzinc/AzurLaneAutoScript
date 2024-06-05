/* eslint-env node */

import {chrome} from '../../electron-vendors.config.json';
import vue from '@vitejs/plugin-vue';
import {renderer} from 'unplugin-auto-expose';
import {join, resolve} from 'node:path';
import {injectAppVersion} from '../../version/inject-app-version-plugin.mjs';
import {vitePluginForArco} from '@arco-plugins/vite-vue';
import UnoCSS from 'unocss/vite';
import AutoImport from 'unplugin-auto-import/vite';
import Components from 'unplugin-vue-components/vite';
import {ArcoResolver} from 'unplugin-vue-components/resolvers';

/**
 * https://github.com/arco-design/arco-plugins/blob/main/packages/plugin-vite-react/README.md
 */
import VueI18nPlugin from '@intlify/unplugin-vue-i18n/vite';

// your plugin installation

const PACKAGE_ROOT = __dirname;
const PROJECT_ROOT = join(PACKAGE_ROOT, '../..');

/**
 * @type {import('vite').UserConfig}
 * @see https://vitejs.dev/config/
 */
const config = {
  mode: process.env.MODE,
  root: PACKAGE_ROOT,
  envDir: PROJECT_ROOT,
  resolve: {
    alias: [
      {
        find: '/@/',
        replacement: join(PACKAGE_ROOT, 'src') + '/',
      },
      {
        find: 'vue-i18n',
        replacement: 'vue-i18n/dist/vue-i18n.cjs.js',
      },
      {
        find: '@common',
        replacement: join(PACKAGE_ROOT, '../common') + '/',
      },
    ],
  },
  base: '',
  server: {
    fs: {
      strict: true,
    },
  },
  build: {
    sourcemap: true,
    target: `chrome${chrome}`,
    outDir: 'dist',
    assetsDir: '.',
    rollupOptions: {
      input: join(PACKAGE_ROOT, 'index.html'),
    },
    emptyOutDir: true,
    reportCompressedSize: false,
  },
  test: {
    environment: 'happy-dom',
  },
  css: {
    preprocessorOptions: {
      less: {
        javascriptEnabled: true,
      },
    },
  },
  plugins: [
    vue(),
    renderer.vite({
      preloadEntry: join(PACKAGE_ROOT, '../preload/src/index.ts'),
    }),
    injectAppVersion(),
    AutoImport({
      resolvers: [ArcoResolver()],
    }),
    Components({
      resolvers: [
        ArcoResolver({
          sideEffect: true,
        }),
      ],
    }),
    new vitePluginForArco({
      theme: '@arco-themes/vue-am-alas',
    }),
    VueI18nPlugin({
      include: resolve(PACKAGE_ROOT, './src/locales/lang/**'),
    }),
    UnoCSS({
      configFile: './uno.config.ts',
    }),
  ],
  optimizeDeps: {
    include: [
      '@arco-design/web-vue/es/locale/lang/zh-cn',
      '@arco-design/web-vue/es/locale/lang/en-us',
      '@arco-design/web-vue/es/locale/lang/ja-jp',
      '@arco-design/web-vue/es/locale/lang/zh-tw',
    ],
  },
};

export default config;
