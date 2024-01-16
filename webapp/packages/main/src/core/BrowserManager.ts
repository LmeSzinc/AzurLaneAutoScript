import type {App} from './App';
import type {BrowserWindowOpts} from '@/core/Browser';
import Browser from '@/core/Browser';
import type {MainEvents} from '@alas/common';

export default class BrowserManager {
  app: App;

  browsers: Map<string, Browser | null> = new Map();

  constructor(app: App) {
    this.app = app;
  }

  /**
   * 启动或初始化
   * @param options
   */
  retrieveOrInitialize(options: BrowserWindowOpts) {
    let browser = this.browsers.get(options.identifier);
    if (browser) {
      return browser;
    }
    this.app.logger.info('create browser:' + options.identifier);
    browser = new Browser(options, this.app);

    // 监听 fetch 方法

    this.browsers.set(options.identifier, browser);

    return browser;
  }

  broadcast<T extends keyof MainEvents>(eventName: T, data?: MainEvents[T]) {
    this.browsers.forEach(browser => {
      browser?.dispatchEvent(eventName, data);
    });
  }
}
