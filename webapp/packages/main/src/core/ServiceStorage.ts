// import { logAfter, logBefore } from './Logger';

/**
 * 存储插件中的 service
 */
export class ServiceStorage {
  static services: WeakMap<any, {name: string; methodName: string; showLog?: boolean}[]> =
    new WeakMap();

  /**
   * 处理所有服务的初始化
   */
  // @logBefore('[服务]初始化服务...')
  // @logAfter('[服务]初始化完成!')
  init() {
    // 服务上桥
    // global.services = {
    //   user: this.user,
    //   system: this.system,
    // };
    // 检查 macOS 权限上桥
    // ipcMain.handle(
    //   CHANNELS.CHECK_ACCESSIBILITY_FOR_MAC_OS,
    //   this.system.checkAccessibilityForMacOS,
    // );
  }
}
