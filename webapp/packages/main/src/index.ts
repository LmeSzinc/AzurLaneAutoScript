import {app} from 'electron';
import './security-restrictions';
import {restoreWindow} from '/@/mainWindow';
// import {platform} from 'node:process';

/**
 * Prevent electron from running multiple instances.
 */
const isSingleInstance = app.requestSingleInstanceLock();
if (!isSingleInstance) {
  app.quit();
  process.exit(0);
}
app.on('second-instance', restoreWindow);

/**
 * Disable Hardware Acceleration to save more system resources.
 * Also `in-process-gpu` to avoid creating a gpu process which may `exited unexpectedly`
 * See https://github.com/electron/electron/issues/30966
 */
app.disableHardwareAcceleration();
app.commandLine.appendSwitch('disable-gpu');
app.commandLine.appendSwitch('disable-software-rasterizer');
app.commandLine.appendSwitch('disable-gpu-compositing');
app.commandLine.appendSwitch('disable-gpu-rasterization');
app.commandLine.appendSwitch('disable-gpu-sandbox');
app.commandLine.appendSwitch('in-process-gpu');
/**
 * Shout down background process if all windows was closed
 */
// app.on('window-all-closed', () => {
//   if (platform !== 'darwin') {
//     app.quit();
//   }
// });

/**
 * @see https://www.electronjs.org/docs/latest/api/app#event-activate-macos Event: 'activate'.
 */
// app.on('activate', createWindow);
/**
 * Create the application window when the background process is ready.
 */
// app
//   .whenReady()
//   .then(createWindow)
//   .then(loadURL)
//   .catch(e => console.error('Failed create window:', e));

/**
 * Install Vue.js or any other extension in development mode only.
 * Note: You must install `electron-devtools-installer` manually
 */
// if (import.meta.env.DEV) {
//   app
//     .whenReady()
//     .then(() => import('electron-devtools-installer'))
//     .then(module => {
//       const {default: installExtension, VUEJS3_DEVTOOLS} =
//         // @ts-expect-error Hotfix for https://github.com/cawa-93/vite-electron-builder/issues/915
//         typeof module.default === 'function' ? module : (module.default as typeof module);
//
//       return installExtension(VUEJS3_DEVTOOLS, {
//         loadExtensionOptions: {
//           allowFileAccess: true,
//         },
//       });
//     })
//     .catch(e => console.error('Failed install extension:', e));
// }

/**
 * Check for app updates, install it in background and notify user that new version was installed.
 * No reason run this in non-production build.
 * @see https://www.electron.build/auto-update.html#quick-setup-guide
 *
 * Note: It may throw "ENOENT: no such file app-update.yml"
 * if you compile production app without publishing it to distribution server.
 * Like `npm run compile` does. It's ok 😅
 */
// if (import.meta.env.PROD) {
//   app
//     .whenReady()
//     .then(() => import('electron-updater'))
//     .then(module => {
//       const autoUpdater =
//         module.autoUpdater ||
//         // @ts-expect-error Hotfix for https://github.com/electron-userland/electron-builder/issues/7338
//         (module.default.autoUpdater as (typeof module)['autoUpdater']);
//       return autoUpdater.checkForUpdatesAndNotify();
//     })
//     .catch(e => console.error('Failed check and install updates:', e));
// }

/**
 *  1. app 实例相关创建监听在这里问完成
 *  2. 此处补充 createApp 内部相关需要的窗口和服务事件
 */
app.whenReady().then(() => {
  /**
   * TODO createAPP
   */
});
