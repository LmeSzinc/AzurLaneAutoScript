import {createMainWindow} from '/@/createMainWindow';
import {addIpcMainListener} from '/@/addIpcMainListener';
import {CoreService} from '/@/coreService';
import logger from '/@/logger';
import {app, nativeImage, Tray} from 'electron';
import {join} from 'node:path';
import {isMacintosh} from '@common/utils';
export const createApp = async () => {
  logger.info('-----createApp-----');
  logger.info('-----createMainWindow-----');
  const mainWindow = await createMainWindow();
  const coreService = new CoreService({mainWindow});

  // Hide menu
  const {Menu} = require('electron');
  Menu.setApplicationMenu(null);
  const icon = nativeImage.createFromPath(join(__dirname, './icon.png'));
  const dockerIcon = icon.resize({width: 16, height: 16});
  // Tray
  const tray = new Tray(isMacintosh ? dockerIcon : icon);
  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show',
      click: function () {
        mainWindow?.show();
      },
    },
    {
      label: 'Hide',
      click: function () {
        mainWindow?.hide();
      },
    },
    {
      label: 'Exit',
      click: function () {
        coreService.curService?.kill(() => {
          logger.info('kill coreService');
        });
        app.quit();
        process.exit(0);
      },
    },
  ]);
  tray.setToolTip('Alas');
  tray.setContextMenu(contextMenu);
  tray.on('click', () => {
    if (mainWindow?.isVisible()) {
      if (mainWindow?.isMinimized()) {
        mainWindow?.show();
      } else {
        mainWindow?.hide();
      }
    } else {
      mainWindow?.show();
    }
  });
  tray.on('right-click', () => {
    tray.popUpContextMenu(contextMenu);
  });

  await addIpcMainListener(mainWindow, coreService);
  return {
    mainWindow,
    coreService,
  };
};
