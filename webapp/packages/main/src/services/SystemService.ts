import {AlasConfig, isMacOS} from '@alas/common';
import {systemPreferences} from 'electron';
import {event, ServiceModule} from './index';
import {checkIsFirst} from '@/utils/checkIsFirst';
import {modifyConfigYaml} from '@/utils/modifyConfigYaml';
import {copyFilesToDir} from '@/utils/copyFilesToDir';
import {getAlasConfigDirFiles} from '@/utils/alasConfig';

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
  async getAlasConfig() {
    await this.app.loadAppConfig();
    return this.app.config;
  }

  @event('/system/cache-page-log')
  cachePageLog(level: 'info' | 'error', message: string) {
    const {logger} = this.app;
    logger[level](message);

    return true;
  }

  @event('/system/modify-config-yaml')
  modifyConfigYaml(data: {filePath: string; modifyConfig: AlasConfig}) {
    modifyConfigYaml(data.filePath, data.modifyConfig as any);
    return true;
  }

  @event('/system/get-alas-config-dir-files')
  getAlasConfigDirFiles() {
    return getAlasConfigDirFiles();
  }

  @event('/system/copy-files-to-dir')
  async copyFileToDir(data: {paths: string[]; targetDir: string}) {
    try {
      await copyFilesToDir(data.paths, data.targetDir);
      return true;
    } catch (e) {
      this.app.logger.error(`复制文件失败 ${String(e)}`);
      return false;
    }
  }
}
