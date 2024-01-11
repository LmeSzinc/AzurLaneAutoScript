import {installerArgs, installerPath} from '@/config';
import {PyShell} from '@/pyshell';
import {ServiceModule, event} from '@/services/index';
import {ALAS_RELAUNCH_ARGV} from '@alas/common';

export default class ScriptService extends ServiceModule {
  @event('/script/start-alas-server')
  startScriptServer() {
    /**
     * 启动外部的python脚本服务
     */

    const {app} = this;
    const {config, logger} = app;
    const browser = app.browserManager.browsers.get('index')!;
    const dispatchEvent = browser.dispatchEvent.bind(browser);
    const {webuiPath, webuiArgs} = config;
    if (!webuiPath || !webuiArgs) {
      return false;
    }
    const alas = new PyShell(webuiPath, webuiArgs);
    // 把服务挂在到app上
    this.app.initScriptService(alas);

    /**
     * 监听相关的事件
     */
    alas?.on('error', function (err: string) {
      if (!err) return;
      logger.error('alas.error:' + err);
      dispatchEvent('scriptLog', err);
    });
    alas?.end(function (err) {
      if (!err) return;
      logger.info('alas.end:' + err);
      dispatchEvent('scriptLog', err.message);
    });
    alas?.on('stdout', function (message) {
      dispatchEvent('scriptLog', message);
    });

    alas?.on('message', function (message) {
      dispatchEvent('scriptLog', message);
    });
    alas?.on('stderr', function (message: string) {
      dispatchEvent('scriptLog', message);
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
      logger.error('alas pythonError:' + err);
    });

    return true;
  }

  @event('/script/start-install-server')
  startInstallerServer() {
    if (process.argv.includes(ALAS_RELAUNCH_ARGV)) {
      return false;
    }
    const {app} = this;
    const {logger, initScriptService} = app;
    const browser = app.browserManager.browsers.get('index')!;
    const dispatchEvent = browser.dispatchEvent.bind(browser);
    let installer: PyShell | null = null;
    try {
      installer = new PyShell(installerPath, installerArgs);
    } catch (err) {
      this.app.logger.error('startInstallerServer error:' + err);
      dispatchEvent('scriptLog', err as string);
    }

    installer?.on('error', function (err: string) {
      if (!err) return;
      logger.error('installer.error:' + err);
      dispatchEvent('scriptLog', err);
    });
    installer?.end(function (err) {
      if (!err) return;
      logger.info('installer.end:' + err);
      dispatchEvent('scriptLog', err.message);
    });
    installer?.on('stdout', function (message) {
      dispatchEvent('scriptLog', message);
    });
    installer?.on('message', function (message) {
      dispatchEvent('scriptLog', message);
    });
    installer?.on('stderr', function (message: string) {
      dispatchEvent('scriptLog', message);
    });

    installer?.on('pythonError', err => {
      dispatchEvent('scriptLog', err);
      logger.error('alas pythonError :' + err);
    });
    initScriptService(installer!);
    return true;
  }
}
