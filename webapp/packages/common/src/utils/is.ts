import {osx, windows as _windows, main, renderer} from 'electron-is/is';

/**
 * 判断是否是 mac 平台
 */
export const isMacOS = osx();

/**
 * 判断是否是 windows
 */
export const isWindows = _windows();

export const isMain = main();

export const isRenderer = renderer();

export const isDev = process.env.NODE_ENV === 'development';

export const isTest = process.env.NODE_ENV === 'test';
