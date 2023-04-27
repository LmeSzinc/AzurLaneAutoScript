import {webuiArgs, webuiPath} from '/@/config';
import {PyShell} from '/@/pyshell';
import type {CallbackFun} from '/@/coreService';
import logger from '/@/logger';

export const createAlas: CallbackFun = async ctx => {
  const alas = new PyShell(webuiPath, webuiArgs);
  alas.on('error', function (err: string) {
    logger.error(err);
    ctx.sendLaunchLog(err);
  });
  alas.end(function (err: string) {
    ctx.sendLaunchLog(err);
    logger.error(err);
    if (err) throw err;
  });
  alas.on('stdout', function (message) {
    ctx.sendLaunchLog(message);
  });

  alas.on('message', function (message) {
    ctx.sendLaunchLog(message);
  });
  alas.on('stderr', function (message: string) {
    ctx.sendLaunchLog(message);
    /**
     * Receive logs, judge if Alas is ready
     * For starlette backend, there will have:
     * `INFO:     Uvicorn running on http://0.0.0.0:22267 (Press CTRL+C to quit)`
     * Or backend has started already
     * `[Errno 10048] error while attempting to bind on address ('0.0.0.0', 22267): `
     */
    if (message.includes('Application startup complete') || message.includes('bind on address')) {
      alas.removeAllListeners('stderr');
      alas.removeAllListeners('message');
      alas.removeAllListeners('stdout');
    }
  });
  return alas;
};
