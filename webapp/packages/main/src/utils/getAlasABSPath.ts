import {app} from 'electron';
import {isMacintosh, isWindows} from './env';

/**
 * Get the absolute path of the project root directory
 * @param defDeep
 */
const getAlasABSPath = (defDeep = 0) => {
  const path = require('path');
  const sep = path.sep;
  const fg = require('fast-glob');
  const os = require('os');
  let appAbsPath = app?.getAppPath() || process.execPath || process.cwd();
  if (isWindows) {
    appAbsPath = process.cwd();
  } else if (isMacintosh && import.meta.env.PROD) {
    appAbsPath = app?.getAppPath() || process.execPath;
  }
  const appAbsPathArr = appAbsPath.split(sep);
  let deep = defDeep || appAbsPath.replace(os.homedir(), '').split(sep).length;
  let flag = false;
  let alasABSPath = '';
  while (deep > 0 && !flag) {
    appAbsPathArr.pop();
    const entries = fg.sync(['**/config/deploy.yaml', '**/config/deploy.template.yaml'], {
      dot: true,
      cwd: appAbsPathArr.join(sep) as string,
    });
    if (entries.length > 0) {
      flag = true;
      alasABSPath = appAbsPathArr.join(sep);
    }
    deep--;
  }
  return alasABSPath.endsWith(sep) ? alasABSPath : alasABSPath + sep;
};

export default getAlasABSPath;
