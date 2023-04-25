import type {CallbackFun} from '/@/coreService';
import {app} from 'electron';
import {restoreWindow} from '/@/mainWindow';
import {isMacintosh} from '@common/utils/env';
export const createApp: CallbackFun = async (ctx, next) => {
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
  app.on('window-all-closed', () => {
    if (!isMacintosh) {
      app.quit();
    }
  });

  /**
   * @see https://www.electronjs.org/docs/latest/api/app#event-activate-macos Event: 'activate'.
   */
  isMacintosh &&
    app.on('activate', () => {
      /**
       * 这里有个问题 如果主窗口已经存在了，那么就不需要再次创建了 但是不是很清楚什么情况下需要被触发再次创建主窗口的操作
       */
      ctx.mainWindow && ctx.mainWindow.show();
    });
  isMacintosh &&
    app.on('will-quit', () => {
      ctx.kill();
    });

  /**
   * Create the application window when the background process is ready.
   */
  await app.whenReady();
  next();
};
