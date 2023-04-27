import type {PyShell} from '/@/pyshell';
import {createAlas, createInstaller} from '/@/serviceLogic';
import {ALAS_LOG} from '@common/constant/eventNames';
import {BrowserWindow} from "electron";

export interface CoreServiceOption {
  appABSPath?: string;
  isFirstRun?: boolean;
  theme?: 'light' | 'dark';
  mainWindow: Electron.BrowserWindow | null;
}

const defOptions = {
  appABSPath: '',
  theme: 'light',
  isFirstRun: false,
  mainWindow: BrowserWindow.getAllWindows()[0] || null,
};

export type CallbackFun<T = any> = (
  coreService: CoreService,
  next: (...args: any[]) => Promise<PyShell | null>,
  ...args1: (any | T)[]
) => Promise<PyShell | null>;

export class CoreService {
  public appABSPath: string;
  public theme = 'light';
  public mainWindow: Electron.BrowserWindow | null = null;
  private currentService: PyShell | null = null;
  private eventQueue: Array<CallbackFun> = [createInstaller, createAlas];
  private stepIndex = 0;

  constructor(options?: CoreServiceOption) {
    const {appABSPath, theme, mainWindow} = Object.assign(defOptions, options || {});
    this.appABSPath = appABSPath;
    this.theme = theme;
    this.mainWindow = mainWindow;
  }

  async run(...rags: any[]) {
    const cb = this.eventQueue[this.stepIndex++];
    const next = (...rags1: any[]) => {
      return this.run(...rags1);
    };
    try {
      cb && (this.currentService = await cb(this, next, ...rags));
    } catch (e) {
      /**
       * 1. 事件执行失败，记录日志
       */
      console.error(e);
    }
    return this.curService;
  }

  get curService() {
    return this.currentService;
  }

  reset() {
    this.stepIndex = 0;
  }

  sendLaunchLog(message: string) {
    if (!this.mainWindow || this.mainWindow.isDestroyed()) return;
    this.mainWindow?.webContents.send(ALAS_LOG, message);
  }

  kill(callback?: () => void) {
    this.curService?.kill(callback || this.cb);
  }

  cb() {
    /**
     *
     */
  }
}
