import {event, ServiceModule} from './index';
import {BrowserWindowsIdentifier} from '@alas/common';

const Home = BrowserWindowsIdentifier.home;

export default class BrowserService extends ServiceModule {
  /**
   *
   */
  @event('/browser/window-tray')
  windowTray() {
    const {browserWindow} = this.app.browserManager.browsers.get(Home) || {};
    browserWindow?.hide();
  }

  /**
   * 关闭当前窗口
   */
  @event('/browser/close-current')
  closeWindow() {
    const {destroy} = this.app;
    destroy();
  }

  @event('/browser/minimize-current')
  minimizeWindow() {
    const {browserWindow} = this.app.browserManager.browsers.get(Home) || {};
    browserWindow?.minimize();
  }

  /**
   * 关闭页面会停止所有服务
   */
  @event('/browser/maximize-current')
  maximizeWindow() {
    const {browserWindow} = this.app.browserManager.browsers.get(Home) || {};
    browserWindow?.maximize();
  }
}
