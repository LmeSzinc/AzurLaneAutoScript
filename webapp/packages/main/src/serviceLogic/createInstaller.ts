import type {CallbackFun} from '/@/coreService';
import {PyShell} from '/@/pyshell';
import {installerArgs, installerPath} from '/@/config';
import {ALAS_RELAUNCH_ARGV} from '@common/constant/config';

export const createInstaller: CallbackFun = async (ctx, next) => {
  if (process.argv.includes(ALAS_RELAUNCH_ARGV)) return next();
  const installer = new PyShell(installerPath, installerArgs);
  ctx.setInstaller(installer);
  ctx.installerService?.end(function (err: string) {
    ctx.sendLaunchLog(err);
    if (err) throw err;
  });
  ctx.installerService?.on('stdout', function (message) {
    ctx.sendLaunchLog(message);
  });
  ctx.installerService?.on('message', function (message) {
    ctx.sendLaunchLog(message);
  });
  ctx.installerService?.on('stderr', function (message: string) {
    ctx.sendLaunchLog(message);
  });
};
