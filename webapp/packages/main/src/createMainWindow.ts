import {app, BrowserWindow, globalShortcut, nativeTheme} from 'electron';
import {join} from 'node:path';
import {URL} from 'node:url';
import {ThemeObj} from '@common/constant/theme';
import logger from '/@/logger';

export const createMainWindow = async () => {
  nativeTheme.themeSource = ThemeObj['light'];
  const browserWindow = new BrowserWindow({
    width: 1280,
    height: 880,
    show: false, // Use 'ready-to-show' event to show window
    frame: false,
    icon: join(__dirname, './icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false, // Sandbox disabled because the demo of preload script depend on the Node.js api
      webviewTag: false, // The webview tag is not recommended. Consider alternatives like an iframe or Electron's BrowserView. @see https://www.electronjs.org/docs/latest/api/webview-tag#warning
      preload: join(app.getAppPath(), 'packages/preload/dist/index.cjs'),
    },
  });
  browserWindow.setMinimumSize(576, 396);
  /**
   * If the 'show' property of the BrowserWindow's constructor is omitted from the initialization options,
   * it then defaults to 'true'. This can cause flickering as the window loads the html content,
   * and it also has show problematic behaviour with the closing of the window.
   * Use `show: false` and listen to the  `ready-to-show` event to show the window.
   *
   * @see https://github.com/electron/electron/issues/25012 for the afford mentioned issue.
   */
  browserWindow.on('ready-to-show', () => {
    logger.info('-----ready-to-show-----');
    browserWindow?.show();

    if (import.meta.env.DEV) {
      browserWindow?.webContents.openDevTools();
    }
  });

  browserWindow.on('focus', function () {
    // Dev tools
    globalShortcut.register('Ctrl+Shift+I', function () {
      if (browserWindow?.webContents.isDevToolsOpened()) {
        browserWindow?.webContents.closeDevTools();
      } else {
        browserWindow?.webContents.openDevTools();
      }
    });
    // Refresh
    globalShortcut.register('Ctrl+R', function () {
      browserWindow?.reload();
    });
    globalShortcut.register('Ctrl+Shift+R', function () {
      browserWindow?.reload();
    });
  });
  browserWindow.on('blur', function () {
    globalShortcut.unregisterAll();
  });

  /**
   * URL for main window.
   * Vite dev server for development.
   * `file://../renderer/index.html` for production and test
   */
  const pageUrl =
    import.meta.env.DEV && import.meta.env.VITE_DEV_SERVER_URL !== undefined
      ? import.meta.env.VITE_DEV_SERVER_URL
      : new URL('../renderer/dist/index.html', 'file://' + __dirname).toString();
  await browserWindow.loadURL(pageUrl);

  return browserWindow;
};
