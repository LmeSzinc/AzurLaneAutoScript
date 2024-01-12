import {isDev} from '@alas/common';
import chalk from 'chalk';
import {app} from 'electron';
import {arch, cpus, platform, release, totalmem} from 'os';
import osName from 'os-name';

import {getLogger} from './customLogger';
import type {LogLevel, LogScope} from './types';

interface LogInfo {
  level: LogLevel;
  message: string;
  key: LogScope;
}

interface WithLogParams {
  before?: LogInfo | Function;
  after?: LogInfo | Function;
}

export {logAfter, logBefore} from './logDecorator';

export default class Logger {
  private logger = getLogger('main');

  /**
   * 记录系统日志
   */
  logSystemInfo = () => {
    if (isDev) return;

    this.logger.divider('🚀');
    this.logger.info('开始启动 App...');

    this.logger.divider();
    this.logger.info(`操作系统： ${platform()} ${release()}(${arch()})`);
    this.logger.info(`系统版本：${osName()}`);
    this.logger.info(`处理器： ${cpus().length}核`);
    this.logger.info(`总内存： ${(totalmem() / 1024 / 1024 / 1024).toFixed(0)}G`);
    this.logger.info(`安装路径：${app.getAppPath()}`);
    this.logger.divider();
  };

  /**
   * 给对象带上日志切面
   * @param before
   * @param after
   */
  static withLog =
    ({before, after}: WithLogParams) =>
    (func: Function) => {
      if (before) {
        if (typeof before === 'function') {
          before();
        } else {
          const logger = getLogger(before.key);
          logger[before.level](before.message);
        }
      }

      func();

      if (after) {
        if (typeof after === 'function') {
          after();
        } else {
          const logger = getLogger(after.key);
          logger[after.level](after.message);
        }
      }
    };

  info(msg: string) {
    this.logger.info(msg);
  }

  divider(msg: string) {
    this.logger.divider(msg);
  }

  static getLogger = getLogger;

  trace(msg: any, ...arg: any[]) {
    this.logger.trace(msg, ...arg);
  }

  error(msg: any, ...arg: any[]) {
    this.logger.error(msg, ...arg);
  }

  /**
   * 输出格式为: `[moduleName] 这是一条kitchen log...`
   */
  module(moduleName: string, ...args: any[]) {
    console.log(chalk.blue(`[${moduleName}]`), ...args);
  }

  data(...data: any[]) {
    console.log(chalk.grey('[Data]'), ...data);
  }
}
