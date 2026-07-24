import {app, Menu, Tray, BrowserWindow, ipcMain, globalShortcut, powerMonitor} from 'electron';
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

/**
 * 【问题】电脑睡眠/休眠后再唤醒，Alas 桌面端经常白屏，只能重启或手动 Ctrl+R。
 *
 * 【原因】桌面端是 Electron 壳 + iframe 嵌入本机 PyWebIO（127.0.0.1:端口）。
 * 睡眠时 WebSocket/会话会断开，唤醒后壳层不会自动重连，窗口仍在但内容空白。
 * 实测：唤醒后 gui.py 与端口仍正常，浏览器也能打开 WebUI；Ctrl+R 即可恢复。
 * 这是常见场景，与「启动就白屏」（依赖/端口/证书等）不是同一类问题。
 *
 * 【方案】监听系统 resume，防抖后执行 mainWindow.reload()（与现有 Ctrl+R 相同路径），
 * 重建 iframe 与 PyWebIO 会话。延迟用于：Windows 上 resume 可能连发；给本机网络栈一点恢复时间。
 * 若 reload 后仍白屏且浏览器也打不开，则是 Python/webui 进程已挂，需另做探测重启，不在本修复范围。
 * 咕咕嘎嘎
 */
let resumeReloadTimer: ReturnType<typeof setTimeout> | null = null;

function reloadAfterSystemResume() {
  if (resumeReloadTimer) {
    clearTimeout(resumeReloadTimer);
  }
  // 1 秒防抖：合并短时间内多次 resume，并等待本机栈大致就绪
  resumeReloadTimer = setTimeout(() => {
    resumeReloadTimer = null;
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.reload();
    }
  }, 1000);
}

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
  .then(() => {
    // 系统从睡眠/休眠恢复时自动刷新界面，避免常见白屏（见上方 reloadAfterSystemResume 注释）
    powerMonitor.on('resume', reloadAfterSystemResume);
  })
  .catch((e) => console.error('Failed create window:', e));


// Auto-updates
if (import.meta.env.PROD) {
  app.whenReady()
    .then(() => import('electron-updater'))
    .then(({autoUpdater}) => autoUpdater.checkForUpdatesAndNotify())
    .catch((e) => console.error('Failed check updates:', e));
}

