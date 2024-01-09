import { logger } from './customLogger';
import { LogLevel, LogScope } from './types';

const log = (propertyName: string, params: string | LogParams) => {
  // 如果是 纯文本 直接输出
  if (typeof params === 'string') {
    logger.infoWithScope(propertyName as LogScope, params);
  } else {
    // 如果是对象 必须传入三个参数 然后输出
    const { level, message, scope } = params;
    logger[`${level}WithScope`](scope || propertyName, message);
  }
};

interface LogParams {
  message: string;
  scope: LogScope;
  level: LogLevel;
}

/**
 * 在执行前调用 log
 */
export const logBefore =
  (params: string | LogParams) =>
  (target: object, propertyName: string, descriptor: PropertyDescriptor) => {
    const method = descriptor.value;

    descriptor.value = function (...args: any[]) {
      log('main', params);
      return method.apply(this, args);
    };
  };

/**
 * 在执行后调用 log
 */
export const logAfter =
  (params: string | LogParams) =>
  (target: object, propertyName: string, descriptor: PropertyDescriptor) => {
    const method = descriptor.value;

    descriptor.value = function (...args: any[]) {
      try {
        return method.apply(this, args);
      } finally {
        log('main', params);
      }
    };
  };
