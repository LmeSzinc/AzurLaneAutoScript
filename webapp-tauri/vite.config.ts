import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'
import UnoCSS from 'unocss/vite'

// Dev-only API target: the python backend (spawned by the Tauri shell in dev
// mode, or a standalone instance). The SPA uses relative URLs, so without a
// proxy every /api-style call would hit the vite dev server itself, fail,
// and the UI would render raw i18n keys ("Gui.xxx").
const DEV_API_TARGET = process.env.ALAS_DEV_API_TARGET ?? 'http://127.0.0.1:22267';

/** Routes proxied to the backend; '/config' also covers '/configs' and subpaths. */
const DEV_PROXY: Record<string, string> = Object.fromEntries(
  ['/status', '/schema', '/config', '/i18n', '/language', '/theme', '/run', '/stop', '/instance', '/update', '/remote', '/scheduler', '/sse'].map(
    (path) => [path, DEV_API_TARGET],
  ),
);

export default defineConfig({
  plugins: [UnoCSS(), svelte()],
  clearScreen: false,
  server: {
    host: true,
    port: 1420,
    strictPort: true,
    proxy: DEV_PROXY,
    watch: {
      ignored: ['**/src-tauri/**'],
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    target: 'chrome130',
  },
})
