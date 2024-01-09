import type {AlasConfig} from './config';

/**
 * main -> renderer 的广播事件
 */
export interface MainEvents {
  initDatabase: 'loading' | 'failed' | 'success';

  /**
   * scriptLog
   * 脚本log
   */
  scriptLog: string;
}

/**
 * renderer -> main 的请求事件
 */
export interface RendererEvents {
  /**
   * SystemService
   * 检查可用性
   */
  '/system/check-accessibility': boolean;

  /**
   * SystemService
   * 打开开发者工具
   */
  '/system/open-dev-tools': boolean;

  /**
   * SystemService
   * 启动脚本服务
   */
  '/system/start-script-server': boolean;

  /**
   * SystemService
   * 关闭脚本服务
   */
  '/system/stop-script-server': boolean;

  /**
   * SystemService
   * 修改脚本服务的配置
   */
  '/system/change-script-server-config': boolean;

  /**
   * SystemService
   * 校验是否第一次打开需要执行初始化操作
   */
  '/system/is-first-open': boolean;

  /**
   * SystemService
   * 修改配置文件
   */
  '/system/modify-config-yaml': boolean;

  /**
   * SystemService
   * 获取alas配置文件夹下的文件
   */
  '/system/get-alas-config-dir-files': {
    configPath: string;
    files: Array<{name: string; path: string; lastModifyTime: Date}>;
  };

  /**
   * SystemService
   * 复制文件到指定文件夹
   */
  '/system/copy-files-to-dir': boolean;

  /**
   * SystemService
   * 修改系统主题
   */
  '/system/modify-theme': boolean;

  /**
   * SystemService
   * 修改系统主题
   */
  '/system/get-alas-config': AlasConfig;

  /**
   * SystemService
   * 缓存页面log
   */
  '/system/cache-page-log': boolean;

  /**
   * BrowserService
   * 关闭窗口
   */
  '/browser/close-current': void;

  /**
   * BrowserService
   * 最小化窗口
   */
  '/browser/minimize-current': void;

  /**
   * BrowserService
   * 最大化窗口
   */
  '/browser/maximize-current': void;
  /**
   * BrowserService
   * 点击窗口托盘
   */
  '/browser/window-tray': void;

  /**
   * ScriptService
   * 启动alas服务
   */
  '/script/start-alas-server': boolean;

  /**
   * ScriptService
   * 启动安装服务
   */
  '/script/start-install-server': boolean;
}
