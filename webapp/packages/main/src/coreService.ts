import type {PyShell} from '/@/pyshell';
import {createAlas, createInstaller} from '/@/serviceLogic';
import {ALAS_LOG} from '@common/constant/eventNames';
import {BrowserWindow} from 'electron';
import logger from '/@/logger';

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
    logger.info('---------------run---------------');
    logger.info('stepIndex:' + this.stepIndex);
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
      logger.error('currentService:' + (e as unknown as any).toString());
    }
    return this.curService;
  }

  async next(...rags: any[]) {
    return this.run(...rags);
  }

  get curService() {
    return this.currentService;
  }

  onError(e: Error | any) {
    logger.error(`currentServiceIndex:${this.stepIndex}` + (e as unknown as any).toString());
  }

  reset() {
    this.stepIndex = 0;
  }

  sendLaunchLog(message: string) {
    if (!this.mainWindow || this.mainWindow.isDestroyed()) return;
    logger.info(`pyShellLaunch:   ${message}`);
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
