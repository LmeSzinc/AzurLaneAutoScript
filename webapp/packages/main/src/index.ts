import {app, BrowserWindow} from 'electron';
import './security-restrictions';
import {createApp} from '/@/createApp';
import logger from '/@/logger';
import {dpiScaling} from '/@/config';

/**
 * Prevent electron from running multiple instances.
 */
const isSingleInstance = app.requestSingleInstanceLock();
logger.info(`isSingleInstance:${isSingleInstance}`);
if (!isSingleInstance) {
  app.quit();
} else {
  app.on('second-instance', async () => {
    logger.info('second-instance');
    const [curWindow] = BrowserWindow.getAllWindows();
    if (!curWindow) {
      logger.info('------createApp------');
      await createApp();
    } else {
      logger.info('------curWindow.focus------');
      curWindow.focus?.();
    }
  });
}

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
app.commandLine.appendSwitch('no-sandbox');

// No DPI scaling
if (!dpiScaling) {
  app.commandLine.appendSwitch('high-dpi-support', '1');
  app.commandLine.appendSwitch('force-device-scale-factor', '1');
}

/**
 *Set App Error Log Path
 */
// app.setAppLogsPath(join(app.getAppPath(), '/AlasAppError'));

/**
 * Shout down background process if all windows was closed
 */
app.on('window-all-closed', () => {
  app.quit();
});

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

app
  .whenReady()
  .then(createApp)
  .catch(e => {
    logger.error('Failed create window:' + e);
  });

app.on('activate', async () => {
  logger.info('------app activate------');
  const [curWindow] = BrowserWindow.getAllWindows();
  if (!curWindow) {
    logger.info('------createApp------');
    await createApp();
  } else {
    logger.info('------curWindow.focus------');
    curWindow.focus();
  }
});
