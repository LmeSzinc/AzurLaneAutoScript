import {app} from 'electron';
import path, {join} from 'path';
import fs from 'fs';

interface Options {
  deep?: number;
  offset?: number;
}

/**
 * 考虑优化:第一次启动时在启动的根目录下创建一个 .alasrc 文件缓存启动路径 方便于下次启动读取 快速启动
 * 需要考虑 判断是否存只安装一个alas,存在冲突可能性
 * 获取脚本的根路径
 * @param rootFile
 * @param options
 */
export function getScriptRootPath(rootFile: string, options?: Options) {
  const {deep, offset = 0} = {
    ...options,
  };
  const appPath = app.getAppPath();
  const sep = path.sep;

  const pathArr = appPath.split(sep);

  let index = deep || pathArr.length - offset;
  let currentPath = '';
  while (index-- > 0) {
    pathArr.pop();
    currentPath = pathArr.join(sep);
    if (fs.existsSync(join(currentPath, rootFile))) {
      break;
    }
  }

  return currentPath;
}
