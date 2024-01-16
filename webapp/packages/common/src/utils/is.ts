/**
 * 判断是否是 mac 平台
 */
export const isMacOS = process.platform === 'darwin';

/**
 * 判断是否是 windows
 */
export const isWindows = process.platform === 'win32';

export const isDev = !!process.env.IS_DEV || process.env.NODE_ENV === 'development';
