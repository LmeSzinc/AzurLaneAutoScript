<<<<<<< HEAD
import {chrome} from '../../.electron-vendors.cache.json';
import {preload} from 'unplugin-auto-expose';
import {join} from 'node:path';
import {injectAppVersion} from '../../version/inject-app-version-plugin.mjs';

const PACKAGE_ROOT = __dirname;
const PROJECT_ROOT = join(PACKAGE_ROOT, '../..');
=======
import {chrome} from '../../electron-vendors.config.json';
import {join} from 'path';
import {builtinModules} from 'module';

const PACKAGE_ROOT = __dirname;
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0

/**
 * @type {import('vite').UserConfig}
 * @see https://vitejs.dev/config/
 */
const config = {
  mode: process.env.MODE,
  root: PACKAGE_ROOT,
<<<<<<< HEAD
  envDir: PROJECT_ROOT,
  resolve: {
    alias: [
      {
        find: '@common',
        replacement: join(PACKAGE_ROOT, '../common'),
      },
    ],
  },
  build: {
    ssr: true,
=======
  envDir: process.cwd(),
  resolve: {
    alias: {
      '/@/': join(PACKAGE_ROOT, 'src') + '/',
    },
  },
  build: {
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
    sourcemap: 'inline',
    target: `chrome${chrome}`,
    outDir: 'dist',
    assetsDir: '.',
<<<<<<< HEAD
    minify: process.env.MODE !== 'development',
=======
    minify: process.env.MODE === 'development' ? false : 'terser',
    terserOptions: {
      ecma: 2020,
      compress: {
        passes: 2,
      },
      safari10: false,
    },
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
    lib: {
      entry: 'src/index.ts',
      formats: ['cjs'],
    },
    rollupOptions: {
<<<<<<< HEAD
=======
      external: [
        'electron',
        ...builtinModules,
      ],
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
      output: {
        entryFileNames: '[name].cjs',
      },
    },
    emptyOutDir: true,
<<<<<<< HEAD
    reportCompressedSize: false,
  },
  plugins: [preload.vite(), injectAppVersion()],
=======
    brotliSize: false,
  },
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
};

export default config;
