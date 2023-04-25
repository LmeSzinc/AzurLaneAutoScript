import type {CallbackFun} from '/@/coreService';
import {PyShell} from '/@/pyshell';
import {installerArgs, installerPath} from '/@/config';
import {ALAS_LOG, UPDATE_APP} from '@common/constant/constant';

export const createInstaller: CallbackFun = async (ctx, next) => {
  const {mainWindow} = ctx;
  const installer = new PyShell(installerPath, installerArgs);
  ctx.setInstaller(installer);
  installer?.end(function (err: string) {
    sendLaunchLog(err);
    if (err) throw err;
  });
  installer?.on('stdout', function (message) {
    sendLaunchLog(message);
  });
  installer?.on('message', function (message) {
    sendLaunchLog(message);
  });
  installer?.on('stderr', function (message: string) {
    sendLaunchLog(message);
  });

  function sendLaunchLog(message: string) {
    message?.includes(UPDATE_APP) && next();
    mainWindow?.webContents.send(ALAS_LOG, message);
  }
};
