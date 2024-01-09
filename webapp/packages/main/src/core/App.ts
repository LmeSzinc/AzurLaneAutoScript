import {EventEmitter} from 'events';
import BrowserManager from './BrowserManager';
import type {TServiceModule} from '@/services';
import {ServiceStorage} from '@/core/ServiceStorage';
import {app, ipcMain} from 'electron';
import Logger from '@/core/Logger';
import {dev} from 'electron-is';
import {createLogProxy} from '@/utils';
import * as browserItems from '../browserItems';
import {getAlasConfig} from '@/utils/alasConfig';
import type {AlasConfig} from '@alas/common';
import type {PyShell} from '@/pyshell';

const importAll = (r: any) => Object.values(r).map((v: any) => v.default);

export type ServiceMap = Map<string, any>;

export class App extends EventEmitter {
  /**
   * 窗口管理器 后期实现一个初始安装器？
   */
  browserManager: BrowserManager;

  /**
   * app 包含的服务能力
   */
  services: any = new WeakMap();

  /**
   * 日志服务
   */
  logger: Logger;

  /**
   * 承接 webview fetch 的事件表
   */
  serviceEventMap: ServiceMap = new Map();

  /**
   * app 启动的统一配置信息
   */
  config: Partial<AlasConfig> = {};

  /**
   * alas 服务
   */
  scriptManager: Map<string, PyShell> = new Map();

  constructor() {
    super();

    const services: TServiceModule[] = importAll(
      // eslint-disable-next-line @typescript-eslint/ban-ts-comment
      // @ts-ignore
      import.meta.glob('../services/*Service.ts', {eager: true}),
    );

    services.forEach(service => this.addService(service));

    // 批量注册 service 中 event 事件 供 webview 消费
    this.serviceEventMap.forEach((serviceInfo, key) => {
      const {service, methodName} = serviceInfo;

      ipcMain.handle(key, async (e, ...data) => {
        // 输出日志
        this.logger.module('Fetch', key);
        if (data) this.logger.data(...data);

        try {
          return await service[methodName](...data);
        } catch (error) {
          this.logger.error(error);

          return {error: (error as any).message};
        }
      });
    });

    // 启动窗口管理器
    this.browserManager = new BrowserManager(this);

    // 日志系统
    this.logger = new Logger();
  }

  onActivate = () => {
    this.browserManager.browsers.get('index')!.show();
  };

  beforeQuit = () => {
    this.browserManager.browsers.forEach(browser => {
      browser?.destroy();
    });

    /**
     * 这里需要补充关闭alas服务
     */
  };
  /**
   * 启动 app
   */
  bootstrap = async () => {
    await this.beforeInit();

    // 控制单例
    const isSingle = app.requestSingleInstanceLock();
    if (!isSingle) {
      app.exit(0);
    }

    app.whenReady().then(() => {
      // 注册 app 协议
      // createProtocol('app');

      this.logger.logSystemInfo();

      // 载入 browsers
      this.initBrowsers();

      this.logger.info('app 初始化完毕!');
      this.logger.divider('🎉');
      this.logger.info('开始启动 app...');
    });
  };

  /**
   * 添加窗口

   */
  initBrowsers() {
    Object.values(browserItems).forEach(item => {
      this.browserManager.retrieveOrInitialize(item);
    });
  }

  /**
   * 初始化 脚本服务
   * @param service
   */
  initScriptService = (service: PyShell) => {
    this.scriptManager.set(service.name, service);
  };

  /**
   * 添加服务
   * @param ServiceClass
   */
  addService(ServiceClass: TServiceModule) {
    const service = new ServiceClass(this);
    this.services.set(ServiceClass, service);

    ServiceStorage.services.get(ServiceClass)?.forEach(event => {
      // 将 event 装饰器中的对象全部存到 ServiceEventMap 中
      this.serviceEventMap.set(event.name, {
        service,
        methodName: event.methodName,
      });
    });
  }

  /**
   * 初始化之前的操作
   */
  async beforeInit() {
    // 替换报错 logger
    if (!dev()) {
      console.error = createLogProxy('error', Logger.getLogger('error'))(console.error);
    }

    await this.loadAppConfig();
  }

  loadAppConfig = async () => {
    const {logger} = this;
    /**
     * 1. 读取配置文件
     */
    logger.info('开始加载基础的配置信息...');
    this.config = await getAlasConfig();
    /**
     * 2. 将配置信息存储到 config 中
     */

    logger.info('基础的配置信息加载完毕');
  };

  destroy = () => {
    this.beforeQuit();
    app.quit();
  };
}
