import type {PyShell} from '/@/pyshell';
import {app} from 'electron';
import {ALAS_LOG, UPDATE_APP} from '@common/constant/eventNames';
import relaunchApp from '/@/relaunchApp';

export interface CoreServiceOption {
  appABSPath: string;
  isFirstRun: boolean;
  theme: 'light' | 'dark';
}

const defOptions = {
  appABSPath: '',
  theme: 'light',
  isFirstRun: false,
};

export type CallbackFun<T = any> = (
  coreService: CoreService,
  next: (...args: any[]) => void,
  ...args1: (any | T)[]
) => Promise<void>;

export class CoreService {
  public appABSPath: string;
  public theme = 'light';
  public mainWindow: Electron.BrowserWindow | null = null;
  public installerService: PyShell | null = null;
  public alasService: PyShell | null = null;
  private eventQueue: Array<CallbackFun> = [];
  private stepIndex = 0;

  constructor(options?: CoreServiceOption) {
    const {appABSPath, theme} = Object.assign(defOptions, options || {});
    this.appABSPath = appABSPath;
    this.theme = theme;
    this.setAlasService.bind(this);
    this.setInstaller.bind(this);
    this.setMainWindow.bind(this);
    this.sendLaunchLog.bind(this);
  }

  async run(...rags: any[]) {
    const cb = this.eventQueue[this.stepIndex++];
    const next = (...rags1: any[]) => {
      this.run(...rags1);
    };
    try {
      cb && (await cb(this, next, ...rags));
    } catch (e) {
      /**
       * 1. 事件执行失败，记录日志
       */
      console.error(e);
    }
  }

  use(fun: CallbackFun) {
    this.eventQueue.push(fun);
    return this;
  }

  updateConfigInfo(options: CoreServiceOption) {}

  setMainWindow(mainWindow: Electron.BrowserWindow) {
    this.mainWindow = mainWindow;
  }

  closeMainWindow() {
    this.mainWindow?.close();
    this.mainWindow = null;
  }

  setInstaller(installerService: PyShell) {
    this.installerService = installerService;
  }

  killInstaller(cb: (...args: any[]) => void) {
    this.installerService?.kill(cb);
    this.installerService = null;
  }

  setAlasService(alasService: PyShell) {
    this.alasService = alasService;
  }

  sendLaunchLog(message: string) {
    this.mainWindow?.webContents?.send(ALAS_LOG, message);
    if (message?.includes(UPDATE_APP)) {
      relaunchApp();
      this.kill(false);
    }
  }

  killAlas(cb: (...args: any[]) => void) {
    this.alasService?.kill(cb);
    this.alasService = null;
  }

  kill(isQuit = true) {
    this.killInstaller(this.cb);
    this.killAlas(this.cb);
    // this.mainWindow?.close();
    isQuit ? app.quit() : app.exit(0);
    process.exit(0);
  }

  cb() {
    /**
     *
     */
  }
}
