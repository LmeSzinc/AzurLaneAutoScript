import type {CoreService} from '/@/coreService';
import type {BrowserWindow} from 'electron';
import {app, ipcMain, nativeTheme} from 'electron';
import {
  ELECTRON_THEME,
  INSTALLER_READY,
  PAGE_ERROR,
  WINDOW_READY,
} from '@common/constant/eventNames';
import {ThemeObj} from '@common/constant/theme';
import logger from '/@/logger';

export const addIpcMainListener = async (mainWindow: BrowserWindow, coreService: CoreService) => {
  // Minimize, maximize, close window.
  ipcMain.on('window-tray', function () {
    mainWindow?.hide();
  });
  ipcMain.on('window-minimize', function () {
    mainWindow?.minimize();
  });
  ipcMain.on('window-maximize', function () {
    mainWindow?.isMaximized() ? mainWindow?.restore() : mainWindow?.maximize();
  });
  ipcMain.on('window-close', function () {
    coreService?.kill();
    mainWindow?.close();
    app.exit(0);
  });

  ipcMain.on(WINDOW_READY, async function (_, args) {
    logger.info('-----WINDOW_READY-----');
    args && (await coreService.run());
  });

  ipcMain.on(INSTALLER_READY, function () {
    logger.info('-----INSTALLER_READY-----');
    coreService.run();
  });

  ipcMain.on(ELECTRON_THEME, (_, args) => {
    logger.info('-----ELECTRON_THEME-----');
    nativeTheme.themeSource = ThemeObj[args];
  });

  ipcMain.on(PAGE_ERROR, (_, args) => {
    logger.info('-----PAGE_ERROR-----');
    logger.error(args);
  });
};
