import type {CopyOptions} from 'fs-extra';
import fsExtra from 'fs-extra';
import {join, sep, normalize} from 'path';

export interface CopyToDirOptions {
  successCallback?: (pathStr: string) => void;
  filedCallback?: (pathStr: string, error: any) => void;
  fsExtraOptions?: CopyOptions;
}

/**
 *
 * @param pathList
 * @param targetDirPath
 * @param options
 */
export async function copyFilesToDir(
  pathList: string[],
  targetDirPath: string,
  options?: CopyToDirOptions | undefined,
) {
  const {fsExtraOptions, successCallback, filedCallback} = options || {};
  for (const pathStr of pathList) {
    try {
      await fsExtra.copy(
        pathStr,
        join(normalize(targetDirPath) + sep + pathStr.split(sep).pop()),
        fsExtraOptions,
      );
      successCallback?.(pathStr);
    } catch (err) {
      filedCallback?.(pathStr, err);
    }
  }
}
