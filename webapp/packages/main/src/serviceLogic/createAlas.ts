import {webuiArgs, webuiPath} from '/@/config';
import {PyShell} from '/@/pyshell';
import type {CallbackFun} from '/@/coreService';
import logger from '/@/logger';

export const createAlas: CallbackFun = async ctx => {
  let alas: PyShell | null = null;
  try {
    alas = new PyShell(webuiPath, webuiArgs);
  } catch (e) {
    ctx.onError(e);
  }

  alas?.on('error', function (err: string) {
    if (!err) return;
    logger.error('alas.error:' + err);
    ctx.sendLaunchLog(err);
  });
  alas?.end(function (err: string) {
    if (!err) return;
    logger.info('alas.end:' + err);
    ctx.sendLaunchLog(err);
    throw err;
  });
  alas?.on('stdout', function (message) {
    ctx.sendLaunchLog(message);
  });

  alas?.on('message', function (message) {
    ctx.sendLaunchLog(message);
  });
  alas?.on('stderr', function (message: string) {
    ctx.sendLaunchLog(message);
    /**
     * Receive logs, judge if Alas is ready
     * For starlette backend, there will have:
     * `INFO:     Uvicorn running on http://0.0.0.0:22267 (Press CTRL+C to quit)`
     * Or backend has started already
     * `[Errno 10048] error while attempting to bind on address ('0.0.0.0', 22267): `
     */
    if (message.includes('Application startup complete') || message.includes('bind on address')) {
      alas?.removeAllListeners('stderr');
      alas?.removeAllListeners('message');
      alas?.removeAllListeners('stdout');
    }
  });

  alas?.on('pythonError', err => {
    ctx.onError('alas pythonError:' + err);
  });
  return alas;
};
