import {app} from 'electron';
import {isMacintosh} from './env';
import fs from 'fs';
/**
 * Get the absolute path of the project root directory
 * @param files
 * @param rootName
 */
const getAlasABSPath = (
  files: string[] = ['**/config/deploy.yaml', '**/config/deploy.template.yaml'],
  rootName: string | string[] = ['AzurLaneAutoScript', 'Alas'],
) => {
  const path = require('path');
  const sep = path.sep;
  const fg = require('fast-glob');
  let appAbsPath = process.cwd();
  if (isMacintosh && import.meta.env.PROD) {
    appAbsPath = app?.getAppPath() || process.execPath;
  }

  while (fs.lstatSync(appAbsPath).isFile()) {
    appAbsPath = appAbsPath.split(sep).slice(0, -1).join(sep);
  }

  let alasABSPath = '';

  let hasRootName = false;

  if (typeof rootName === 'string') {
    hasRootName = appAbsPath.includes(rootName);
  } else if (Array.isArray(rootName)) {
    hasRootName = rootName.some(item =>
      appAbsPath.toLocaleLowerCase().includes(item.toLocaleLowerCase()),
    );
  }

  if (hasRootName) {
    const appAbsPathArr = appAbsPath.split(sep);
    let flag = false;
    while (hasRootName && !flag) {
      const entries = fg.sync(files, {
        dot: true,
        cwd: appAbsPathArr.join(sep) as string,
      });
      if (entries.length > 0) {
        flag = true;
        alasABSPath = appAbsPathArr.join(sep);
      }
      appAbsPathArr.pop();
    }
  } else {
    let step = 4;
    const appAbsPathArr = appAbsPath.split(sep);
    let flag = false;
    while (step > 0 && !flag) {
      appAbsPathArr.pop();
      const entries = fg.sync(files, {
        dot: true,
        cwd: appAbsPathArr.join(sep) as string,
      });
      if (entries.length > 0) {
        flag = true;
        alasABSPath = appAbsPathArr.join(sep);
      }
      step--;
    }
  }

  return alasABSPath.endsWith(sep) ? alasABSPath : alasABSPath + sep;
};

export default getAlasABSPath;
