import {webuiArgs, webuiPath} from '/@/config';
import {PyShell} from '/@/pyshell';
import type {CallbackFun} from '/@/coreService';

export const createAlas: CallbackFun = async (ctx, next) => {
  const {setAlasService, sendLaunchLog} = ctx;
  const alas = new PyShell(webuiPath, webuiArgs);
  setAlasService(alas);
  alas?.end(function (err: string) {
    sendLaunchLog(err);
    if (err) throw err;
  });
  alas?.on('stdout', function (message) {
    sendLaunchLog(message);
  });

  alas?.on('message', function (message) {
    sendLaunchLog(message);
  });
  alas?.on('stderr', function (message: string) {
    sendLaunchLog(message);
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
  next();
};
