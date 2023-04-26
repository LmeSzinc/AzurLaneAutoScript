import {app, BrowserWindow} from 'electron';
import {isMacintosh} from '@common/utils/env';
export const createApp = async () => {
  const mainWindow = new BrowserWindow({});
  /**
   * Prevent electron from running multiple instances.
   */
  const isSingleInstance = app.requestSingleInstanceLock();
  if (!isSingleInstance) {
    app.quit();
    process.exit(0);
  }
  app.on('second-instance', restoreWindow);

  async function restoreWindow() {
    // Someone tried to run a second instance, we should focus our window.
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      if (mainWindow.isVisible()) mainWindow.show();
      mainWindow.focus();
    }
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
  app.on('activate', () => {
    if (mainWindow) {
      mainWindow.show();
      return;
    }
  });
  isMacintosh && app.on('will-quit', () => {});
};
