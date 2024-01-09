import {isMacOS} from '@alas/common';
import {systemPreferences} from 'electron';
import {event, ServiceModule} from './index';
import {checkIsFirst} from '@/utils/checkIsFirst';

export default class SystemService extends ServiceModule {
  /**
   * 检查可用性
   */
  @event('/system/check-accessibility')
  checkAccessibilityForMacOS() {
    if (!isMacOS) return;
    return systemPreferences.isTrustedAccessibilityClient(true);
  }

  @event('/system/open-dev-tools')
  openDevTools() {
    const {browserWindow} = this.app.browserManager.browsers.get('home') || {};
    if (browserWindow?.webContents.isDevToolsOpened()) {
      browserWindow?.webContents.closeDevTools();
    } else {
      browserWindow?.webContents.openDevTools();
    }

    return true;
  }

  @event('/system/start-script-server')
  startScriptServer() {
    /**
     * 启动外部的python脚本服务
     */

    const {app} = this;
    const {config} = app;

    const {} = config;

    return true;
  }

  @event('/system/stop-script-server')
  stopScriptServer() {
    /**
     * 关闭外部的python脚本服务
     */
    return true;
  }

  @event('/system/change-script-server-config')
  changeScriptServerConfig() {
    /**
     * 修改外部的python脚本服务的配置
     */
    const {logger} = this.app;

    try {
      /**
       * 进行相关的修改操作
       */
    } catch (e) {
      logger.error(`修改外部的python脚本服务的配置失败 ${String(e)}`);
      return false;
    }

    return true;
  }

  @event('/system/is-first-open')
  checkIsFirstOpen() {
    return checkIsFirst();
  }

  @event('/system/get-alas-config')
  getAlasConfig() {
    return this.app.config;
  }

  @event('/system/cache-page-log')
  cachePageLog(level: 'info' | 'error', message: string) {
    const {logger} = this.app;
    logger[level](message);

    return true;
  }
}
