import type {BrowserWindowConstructorOptions} from 'electron';
import {protocol, app, Menu, BrowserWindow, globalShortcut, nativeImage, Tray} from 'electron';
import type {BrowserWindowsIdentifier, MainEvents} from '@alas/common';
import EventEmitter from 'events';
import type {App} from '@/core/App';
import {isDev, isMacOS} from '@alas/common';
import {dev} from 'electron-is';
import {join} from 'node:path';

protocol.registerSchemesAsPrivileged([{scheme: 'app', privileges: {secure: true, standard: true}}]);

export interface BrowserWindowOpts extends BrowserWindowConstructorOptions {
  /**
   * URL
   */
  identifier: BrowserWindowsIdentifier;
  title?: string;
  width?: number;
  height?: number;
  devTools?: boolean;
}

export default class Browser extends EventEmitter {
  /**
   * 外部的 app
   * @private
   */
  private app: App;
  /**
   * 内部的 electron 窗口
   * @private
   */
  private _browserWindow?: BrowserWindow;

  /**
   * 标识符
   */
  identifier: string;

  /**
   * 生成时的选项
   */
  options: BrowserWindowOpts;

  /**
   * 对外暴露的获取窗口的方法
   */
  get browserWindow() {
    return this.retrieveOrInitialize();
  }

  /**
   * 构建 BrowserWindows 对象的方法
   * @param options
   * @param application
   */
  constructor(options: BrowserWindowOpts, application: App) {
    super();
    this.app = application;
    this.identifier = options.identifier;
    this.options = options;

    // 初始化
    this.retrieveOrInitialize();

    // 当关闭时将窗口实例销毁
    this.browserWindow.on('closed', () => {
      this.destroy();
    });
  }

  /**
   * 加载地址路径
   * @param name name 在 renderer 中的路径名称
   * @param count 重试次数
   */
  loadUrl = (name: BrowserWindowsIdentifier, count = 1) => {
    if (count > 10) return;
    if (isDev) {
      // this.browserWindow.loadURL(`http://localhost:5173/${name}.html`);
      this.app.logger.info('http://localhost:7777/');
      this.browserWindow.loadURL('http://localhost:7777/').catch(_ => {
        /**
         * 暂时没有想到更好解决方案
         */
        setTimeout(() => {
          this.loadUrl(name, ++count);
        }, 2000);
      });
    } else {
      this.browserWindow.loadURL(`app://./${name}.html`);
    }
  };
  /**
   * 加载托盘
   */
  loadTray = () => {
    const {browserWindow} = this;
    Menu.setApplicationMenu(null);
    const icon = nativeImage.createFromPath(join(__dirname, './icon.png'));
    const dockerIcon = icon.resize({width: 16, height: 16});
    const tray = new Tray(isMacOS ? dockerIcon : icon);
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
          /**
           * 贯标alasService
           */

          app.quit();
          process.exit(0);
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
  };

  /**
   * 加载 Dev 工具
   */
  loadDevTools = () => {
    // 生产环境直接结束
    if (!(dev() || process.env.DEBUG === '1')) return;

    app.whenReady().then(() => {
      const {
        default: installExtension,
        VUEJS3_DEVTOOLS,
        /**
         *  electron-devtools-installer 安装部分依赖会报错 VUEJS3_DEVTOOLS 相关在谷歌商店中的id似乎有变动导致
         */
        // eslint-disable-next-line global-require
      } = require('electron-devtools-installer');

      const extensions = [VUEJS3_DEVTOOLS];

      try {
        installExtension(extensions).then((name: string) => {
          this.app.logger.trace(`Added Extension:  ${name}`);
        });
      } catch (e) {
        this.app.logger.error('An error occurred: ', e);
      }
    });
  };

  /**
   * 加载 窗口事件
   */
  loadActions = () => {
    this.browserWindow.on('focus', () => {
      // Dev tools
      globalShortcut.register('Ctrl+Shift+I', () => {
        if (this.browserWindow.webContents.isDevToolsOpened()) {
          this.browserWindow.webContents.closeDevTools();
        } else {
          this.browserWindow.webContents.openDevTools();
        }
      });

      // Refresh
      globalShortcut.register('Ctrl+R', () => {
        this.browserWindow.reload();
      });
      globalShortcut.register('Ctrl+Shift+R', () => {
        this.browserWindow.reload();
      });
    });

    this.browserWindow.on('blur', () => {
      globalShortcut.unregisterAll();
    });
  };

  show() {
    this.browserWindow.show();
  }

  hide() {
    this.browserWindow.hide();
  }

  /**
   * 销毁实例
   */
  destroy() {
    this._browserWindow = undefined;
  }

  /**
   * 初始化
   */
  retrieveOrInitialize() {
    // 当有这个窗口 且这个窗口没有被注销时
    if (this._browserWindow && !this._browserWindow.isDestroyed()) {
      return this._browserWindow;
    }

    const {identifier, title, width, height, devTools, ...res} = this.options;

    this._browserWindow = new BrowserWindow({
      ...res,
      width,
      height,
      title,
      icon: join(__dirname, './icon.png'),
      // 隐藏默认的框架栏 包括页面名称以及关闭按钮等
      frame: false,
      webPreferences: {
        nodeIntegration: false,
        sandbox: false,
        webviewTag: false,
        // 上下文隔离环境
        // https://www.electronjs.org/docs/tutorial/context-isolation
        contextIsolation: true,
        // devTools: isDev,
        preload: join(app.getAppPath(), '../preload/dist/index.js'),
      },
    });

    this._browserWindow.setMinimumSize(576, 396);

    this.loadTray();
    // this.loadMenu();
    this.loadUrl(identifier);
    // this.loadDevTools();
    this.loadActions();

    // 显示 devtools 就打开
    if (devTools) {
      this._browserWindow.webContents.openDevTools();
    }
    return this._browserWindow;
  }

  /**
   * 向 webview 派发事件
   * @param eventName
   * @param data
   */
  dispatchEvent<T extends keyof MainEvents>(eventName: T, data?: MainEvents[T]) {
    let tempName = Math.random().toString(36).slice(-8);

    tempName = `a_${tempName}`;

    this.browserWindow.webContents.executeJavaScript(`
        const ${tempName} = new Event('electron:${eventName}');
        ${tempName}.data = ${JSON.stringify(data)};
        window.dispatchEvent(${tempName});
     `);
  }
}
