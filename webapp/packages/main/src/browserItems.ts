import type {BrowserWindowOpts} from '@/core/Browser';
import {BrowserWindowsIdentifier} from '@alas/common';
import {join} from 'path';
import {getResources} from '@/utils/getResources';

export const home: BrowserWindowOpts = {
  identifier: BrowserWindowsIdentifier.home,
  width: 1280,
  height: 880,
  devTools: false,
  center: true,
  icon: getResources('icon.png'),
  // 隐藏默认的框架栏 包括页面名称以及关闭按钮等
  frame: false,
  webPreferences: {
    nodeIntegration: false,
    sandbox: false,
    webviewTag: false,
    // 上下文隔离环境
    // https://www.electronjs.org/docs/tutorial/context-isolation
    contextIsolation: true,
    // devTools: isDev,
    preload: join(__dirname, '../preload/index.js'),
  },
};
