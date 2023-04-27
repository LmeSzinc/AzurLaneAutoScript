import {createMainWindow} from '/@/createMainWindow';
import {addIpcMainListener} from '/@/addIpcMainListener';
import {CoreService} from '/@/coreService';
import logger from '/@/logger';
export const createApp = async () => {
  logger.info('-----createApp-----');
  logger.info('-----createMainWindow-----');
  const mainWindow = await createMainWindow();
  const coreService = new CoreService({mainWindow});
  await addIpcMainListener(mainWindow, coreService);
  return {
    mainWindow,
    coreService,
  };
};
