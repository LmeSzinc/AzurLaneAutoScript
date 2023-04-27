import type {CallbackFun} from '/@/coreService';
import {PyShell} from '/@/pyshell';
import {installerArgs, installerPath} from '/@/config';
import {ALAS_RELAUNCH_ARGV} from '@common/constant/config';
import logger from '/@/logger';
export const createInstaller: CallbackFun = async (ctx, next) => {
  if (process.argv.includes(ALAS_RELAUNCH_ARGV)) {
    return next();
  }
  const installer = new PyShell(installerPath, installerArgs);
  installer.on('error', function (err: string) {
    logger.error('installer.error:' + err);
    ctx.sendLaunchLog(err);
  });
  installer?.end(function (err: string) {
    logger.error('installer.end' + err);
    ctx.sendLaunchLog(err);
    if (err) throw err;
  });
  installer?.on('stdout', function (message) {
    ctx.sendLaunchLog(message);
  });
  installer?.on('message', function (message) {
    ctx.sendLaunchLog(message);
  });
  installer?.on('stderr', function (message: string) {
    ctx.sendLaunchLog(message);
  });
  return installer;
};
