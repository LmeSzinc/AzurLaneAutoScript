import { Logger as _Logger } from 'log4js';

type Logger = _Logger;

/**
 * 日志范围
 */
export type LogScope = 'database' | 'app' | 'renderer' | 'main' | 'error';
export type LogLevel = 'info' | 'error' | 'trace' | 'warn' | 'debug';

export type GetLogger = (scope?: LogScope) => Logger;

export type LogWithScope = (newScope: LogScope, ...args: any[]) => void;
