import logger from 'electron-log';
import {join} from 'node:path';
import {getAlasABSPath} from '@common/utils';
const dayjs = require('dayjs');

logger.transports.file.level = 'info';
logger.transports.file.maxSize = 1024 * 1024;
logger.transports.file.format = '[{y}-{m}-{d} {h}:{i}:{s}.{ms}] [{level}]{scope} {text}';
const dateStr = dayjs(new Date()).format('YYYY-MM-DD');
const logPath = join(getAlasABSPath(), `./log/${dateStr}_webapp.txt`);
logger.transports.file.resolvePath = () => logPath;
export default {
  info(params: string) {
    logger.info(params);
  },
  warn(params: string) {
    logger.warn(params);
  },
  error(params: string) {
    logger.error(params);
  },
  debug(params: string) {
    logger.debug(params);
  },
  verbose(params: string) {
    logger.verbose(params);
  },
  silly(params: string) {
    logger.silly(params);
  },
};
