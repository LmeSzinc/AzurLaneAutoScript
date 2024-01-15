import {isDev} from '@alas/common';
import {app} from 'electron';
import type {Configuration, Layout} from 'log4js';
import {join} from 'path';
import dayjs from 'dayjs';
import {getScriptRootPath} from '@/utils/getScriptRootPath';

const dateStr = dayjs(new Date()).format('YYYY-MM-DD');

const logDir = join(app.getPath('userData'), 'Logs');

const level = isDev ? 'trace' : 'info';

// 自定义日志格式
const layout: Layout = {
  type: 'pattern',
  pattern: '[%p] %d{yyyy-MM-dd hh:mm:ss.SSS} | %m',
};

const config: Configuration = {
  appenders: {
    // 控制台输出
    console: {type: 'console'},
    // 日志文件
    app: {
      type: 'file',
      //  join(logDir, 'app', 'log.log')
      filename: join(getScriptRootPath(), `./log/${dateStr}_webapp.txt`),
      // 日志切割后文件名后缀格式
      pattern: 'yyyy-MM-dd.log',
      layout,
    },
    error: {
      type: 'file',
      filename: join(logDir, 'error', 'log.log'),
      pattern: 'yyyy-MM-dd.log',
    },
  },
  categories: {
    default: {appenders: ['app', 'console'], level},
    app: {appenders: ['app', 'console'], level},
    main: {appenders: ['app', 'console'], level},
    renderer: {appenders: ['app', 'console'], level},
    // 错误日志，输出 error 及以上级别的日志
    error: {appenders: ['error'], level: 'error'},
  },
};

export default config;
