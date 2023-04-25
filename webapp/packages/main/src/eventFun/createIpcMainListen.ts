import type {CallbackFun} from '/@/coreService';
import {ipcMain, nativeTheme} from 'electron';
import {isMacintosh} from '@common/utils/env';
import {INSTALLER_READY, WINDOW_READY} from '@common/constant/eventNames';

export const createIpcMainListen: CallbackFun = async (ctx, next) => {
  const {mainWindow, installerService: installer, alasService: alas} = ctx;
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
    if (isMacintosh) {
      mainWindow?.hide();
      return;
    }
    /**
     * TODO In Mac, the closing event of the main window often does not kill the app completely, but hides in the dock, where the process needs to be killed manually and the Mac needs to be processed additionally
     */
    if (installer) {
      installer?.removeAllListeners('stderr');
      installer?.removeAllListeners('message');
      installer?.removeAllListeners('stdout');
      installer?.kill(function () {
        ctx.killInstaller(() => {
          mainWindow?.close();
        });
      });
      return;
    }
    if (alas) {
      alas?.removeAllListeners('stderr');
      alas?.removeAllListeners('message');
      alas?.removeAllListeners('stdout');
      alas?.kill(function () {
        mainWindow?.close();
      });
    }
    mainWindow?.close();
  });

  ipcMain.on(WINDOW_READY, async function (_, args) {
    args && next();
  });

  ipcMain.on(INSTALLER_READY, function () {
    next();
  });

  ipcMain.on('electron-theme', (_, args) => {
    nativeTheme.themeSource = args;
  });
};
