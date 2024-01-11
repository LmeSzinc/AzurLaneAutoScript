/**
 * 判断是否是 mac 平台
 */
export const isMacOS = process.platform === 'darwin'

/**
 * 判断是否是 windows
 */
export const isWindows = process.platform === 'win32'

export const isMain = process.type === 'browser'

export const isRenderer = process.type === 'renderer'

export const isDev = process.env.NODE_ENV === 'development';

export const isTest = process.env.NODE_ENV === 'test';
