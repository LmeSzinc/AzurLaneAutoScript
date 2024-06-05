<<<<<<< HEAD
import {app, BrowserWindow} from 'electron';
import './security-restrictions';
import {createApp} from '/@/createApp';
import logger from '/@/logger';
import {noSandbox} from '/@/config';

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
=======
import {app, Menu, Tray, BrowserWindow, ipcMain, globalShortcut} from 'electron';
import {URL} from 'url';
import {PyShell} from '/@/pyshell';
import {webuiArgs, webuiPath, dpiScaling} from '/@/config';

const path = require('path');

const isSingleInstance = app.requestSingleInstanceLock();

if (!isSingleInstance) {
  app.quit();
  process.exit(0);
}

app.disableHardwareAcceleration();

// Install "Vue.js devtools"
if (import.meta.env.MODE === 'development') {
  app.whenReady()
    .then(() => import('electron-devtools-installer'))
    .then(({default: installExtension, VUEJS3_DEVTOOLS}) => installExtension(VUEJS3_DEVTOOLS, {
      loadExtensionOptions: {
        allowFileAccess: true,
      },
    }))
    .catch(e => console.error('Failed install extension:', e));
}

/**
 * Load deploy settings and start Alas web server.
 */
let alas = new PyShell(webuiPath, webuiArgs);
alas.end(function (err: string) {
  // if (err) throw err;
});


let mainWindow: BrowserWindow | null = null;

const createWindow = async () => {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 880,
    show: false, // Use 'ready-to-show' event to show window
    frame: false,
    icon: path.join(__dirname, './buildResources/icon.ico'),
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,   // Spectron tests can't work with contextIsolation: true
      nativeWindowOpen: true,
      // preload: join(__dirname, '../../preload/dist/index.cjs'),
    },
  });

  /**
   * If you install `show: true` then it can cause issues when trying to close the window.
   * Use `show: false` and listener events `ready-to-show` to fix these issues.
   *
   * @see https://github.com/electron/electron/issues/25012
   */
  mainWindow.on('ready-to-show', () => {
    mainWindow?.show();

    // Hide menu
    const {Menu} = require('electron');
    Menu.setApplicationMenu(null);

    if (import.meta.env.MODE === 'development') {
      mainWindow?.webContents.openDevTools();
    }
  });

  mainWindow.on('focus', function () {
    // Dev tools
    globalShortcut.register('Ctrl+Shift+I', function () {
      if (mainWindow?.webContents.isDevToolsOpened()) {
        mainWindow?.webContents.closeDevTools()
      } else {
        mainWindow?.webContents.openDevTools()
      }
    });
    // Refresh
    globalShortcut.register('Ctrl+R', function () {
      mainWindow?.reload()
    });
    globalShortcut.register('Ctrl+Shift+R', function () {
      mainWindow?.reload()
    });
  });
  mainWindow.on('blur', function () {
    globalShortcut.unregisterAll()
  });

  // Minimize, maximize, close window.
  ipcMain.on('window-tray', function () {
    mainWindow?.hide();
  });
  ipcMain.on('window-min', function () {
    mainWindow?.minimize();
  });
  ipcMain.on('window-max', function () {
    mainWindow?.isMaximized() ? mainWindow?.restore() : mainWindow?.maximize();
  });
  ipcMain.on('window-close', function () {
    alas.kill(function () {
      mainWindow?.close();
    })
  });

  // Tray
  const tray = new Tray(path.join(__dirname, 'icon.png'));
  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show',
      click: function () {
        mainWindow?.show();
      }
    },
    {
      label: 'Hide',
      click: function () {
        mainWindow?.hide();
      }
    },
    {
      label: 'Exit',
      click: function () {
        alas.kill(function () {
          mainWindow?.close();
        })
      }
    }
  ]);
  tray.setToolTip('Alas');
  tray.setContextMenu(contextMenu);
  tray.on('click', () => {
    mainWindow?.isVisible() ? mainWindow?.hide() : mainWindow?.show()
  });
  tray.on('right-click', () => {
    tray.popUpContextMenu(contextMenu)
  });
};


// No DPI scaling
if (!dpiScaling) {
  app.commandLine.appendSwitch('high-dpi-support', '1');
  app.commandLine.appendSwitch('force-device-scale-factor', '1');
}


function loadURL() {
  /**
   * URL for main window.
   * Vite dev server for development.
   * `file://../renderer/index.html` for production and test
   */
  const pageUrl = import.meta.env.MODE === 'development' && import.meta.env.VITE_DEV_SERVER_URL !== undefined
    ? import.meta.env.VITE_DEV_SERVER_URL
    : new URL('../renderer/dist/index.html', 'file://' + __dirname).toString();

  mainWindow?.loadURL(pageUrl);
}


alas.on('stderr', function (message: string) {
  /**
   * Receive logs, judge if Alas is ready
   * For starlette backend, there will have:
   * `INFO:     Uvicorn running on http://0.0.0.0:22267 (Press CTRL+C to quit)`
   * Or backend has started already
   * `[Errno 10048] error while attempting to bind on address ('0.0.0.0', 22267): `
   */
  if (message.includes('Application startup complete') || message.includes('bind on address')) {
    alas.removeAllListeners('stderr');
    loadURL()
  }
});


app.on('second-instance', () => {
  // Someone tried to run a second instance, we should focus our window.
  if (mainWindow) {
    if (mainWindow.isMinimized()) mainWindow.restore();
    if (!mainWindow.isVisible()) mainWindow.show();
    mainWindow.focus();
  }
});


app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});


app.whenReady()
  .then(createWindow)
  .catch((e) => console.error('Failed create window:', e));


// Auto-updates
if (import.meta.env.PROD) {
  app.whenReady()
    .then(() => import('electron-updater'))
    .then(({autoUpdater}) => autoUpdater.checkForUpdatesAndNotify())
    .catch((e) => console.error('Failed check updates:', e));
}

>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
