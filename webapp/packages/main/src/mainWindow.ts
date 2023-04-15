import {app, BrowserWindow, globalShortcut, ipcMain, Menu, nativeTheme, Tray} from 'electron';
import {URL} from 'node:url';
import {PyShell} from '/@/pyshell';
import {dpiScaling, webuiTheme, webuiArgs, webuiPath} from '/@/config';

const path = require('path');
/**
 * Load deploy settings and start Alas web server.
 */
let alas: PyShell | null = null;

let browserWindow: BrowserWindow | null = null;

try {
    nativeTheme.themeSource = webuiTheme;
} catch (e) {
    console.log(e);
}

export async function createWindow() {
    browserWindow = new BrowserWindow({
        width: 1280,
        height: 880,
        show: false, // Use 'ready-to-show' event to show window
        frame: false,
        icon: path.join(__dirname, './icon.png'),
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            sandbox: false, // Sandbox disabled because the demo of preload script depend on the Node.js api
            webviewTag: false, // The webview tag is not recommended. Consider alternatives like an iframe or Electron's BrowserView. @see https://www.electronjs.org/docs/latest/api/webview-tag#warning
            // preload: path.join(app.getAppPath(), 'packages/preload/dist/index.cjs'),
        },
    });


    /**
     * If the 'show' property of the BrowserWindow's constructor is omitted from the initialization options,
     * it then defaults to 'true'. This can cause flickering as the window loads the html content,
     * and it also has show problematic behaviour with the closing of the window.
     * Use `show: false` and listen to the  `ready-to-show` event to show the window.
     *
     * @see https://github.com/electron/electron/issues/25012 for the afford mentioned issue.
     */
    browserWindow.on('ready-to-show', () => {
        browserWindow?.show();

        // Hide menu
        const {Menu} = require('electron');
        Menu.setApplicationMenu(null);

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


    ipcMain.on('window-ready', function (_, args) {
        args && initWindowEvents();
    });

    // Tray
    const tray = new Tray(path.join(__dirname, 'icon.png'));
    const contextMenu = Menu.buildFromTemplate([
        {
            label: 'Show',
            click: function () {
                browserWindow?.show();
            },
        },
        {
            label: 'Hide',
            click: function () {
                browserWindow?.hide();
            },
        },
        {
            label: 'Exit',
            click: function () {
                alas?.kill(function () {
                    browserWindow?.close();
                });
            },
        },
    ]);
    tray.setToolTip('Alas');
    tray.setContextMenu(contextMenu);
    tray.on('click', () => {
        if (browserWindow?.isVisible()) {
            if (browserWindow?.isMinimized()) {
                browserWindow?.show();
            } else {
                browserWindow?.hide();
            }
        } else {
            browserWindow?.show();
        }
    });
    tray.on('right-click', () => {
        tray.popUpContextMenu(contextMenu);
    });
}

// No DPI scaling
if (!dpiScaling) {
    app.commandLine.appendSwitch('high-dpi-support', '1');
    app.commandLine.appendSwitch('force-device-scale-factor', '1');
}


export function loadURL() {
    /**
     * URL for main window.
     * Vite dev server for development.
     * `file://../renderer/index.html` for production and test
     */
    const pageUrl =
        import.meta.env.DEV && import.meta.env.VITE_DEV_SERVER_URL !== undefined
            ? import.meta.env.VITE_DEV_SERVER_URL
            : new URL('../renderer/dist/index.html', 'file://' + __dirname).toString();

    browserWindow?.loadURL(pageUrl);
}

function initWindowEvents() {
    alas = new PyShell(import.meta.env.DEV ? path.join('./', webuiPath) : webuiPath, webuiArgs);

    // Minimize, maximize, close window.
    ipcMain.on('window-tray', function () {
        browserWindow?.hide();
    });
    ipcMain.on('window-min', function () {
        browserWindow?.minimize();
    });
    ipcMain.on('window-max', function () {
        browserWindow?.isMaximized() ? browserWindow?.restore() : browserWindow?.maximize();
    });
    ipcMain.on('window-close', function () {
        alas?.removeAllListeners('stderr');
        alas?.removeAllListeners('message');
        alas?.removeAllListeners('stdout');
        alas?.kill(function () {
            browserWindow?.close();
            browserWindow = null;
        });

    });


    alas?.end(function (/* err: string */) {
        // if (err) throw err;
    });
    alas?.on('stdout', function (message) {
        browserWindow?.webContents.send('alas-log', message);
    });

    alas?.on('message', function (message) {
        browserWindow?.webContents.send('alas-log', message);
    });
    alas?.on('stderr', function (message: string) {
        /**
         * Receive logs, judge if Alas is ready
         * For starlette backend, there will have:
         * `INFO:     Uvicorn running on http://0.0.0.0:22267 (Press CTRL+C to quit)`
         * Or backend has started already
         * `[Errno 10048] error while attempting to bind on address ('0.0.0.0', 22267): `
         */
        browserWindow?.webContents.send('alas-log', message);
        if (message.includes('Application startup complete') || message.includes('bind on address')) {
            alas?.removeAllListeners('stderr');
            alas?.removeAllListeners('message');
            alas?.removeAllListeners('stdout');
            // loadURL();
        }
    });
}


export async function restoreWindow() {
    // Someone tried to run a second instance, we should focus our window.
    if (browserWindow) {
        if (browserWindow.isMinimized()) browserWindow.restore();
        if (!browserWindow.isVisible()) browserWindow.show();
        browserWindow.focus();
    }
}
