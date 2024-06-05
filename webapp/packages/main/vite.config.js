<<<<<<< HEAD
import {node} from '../../.electron-vendors.cache.json';
import {join} from 'node:path';
import {injectAppVersion} from '../../version/inject-app-version-plugin.mjs';

const PACKAGE_ROOT = __dirname;
const PROJECT_ROOT = join(PACKAGE_ROOT, '../..');
=======
import {node} from '../../electron-vendors.config.json';
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
    alias: {
      '/@/': join(PACKAGE_ROOT, 'src') + '/',
      '@common': join(PACKAGE_ROOT, '../common/'),
    },
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
    target: `node${node}`,
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
        'electron-devtools-installer',
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
  plugins: [injectAppVersion()],
=======
    brotliSize: false,
  },
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
};

export default config;
