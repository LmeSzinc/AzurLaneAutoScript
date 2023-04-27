import {createMainWindow} from '/@/createMainWindow';
import {addIpcMainListener} from '/@/addIpcMainListener';
import {CoreService} from '/@/coreService';
export const createApp = async () => {
  const mainWindow = await createMainWindow();
  const coreService = new CoreService({mainWindow});
  await addIpcMainListener(mainWindow, coreService);
};
