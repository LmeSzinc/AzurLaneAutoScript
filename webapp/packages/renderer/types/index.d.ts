import type {BinaryLike} from 'node:crypto';
import type {AlasConfig} from '../../preload/src/alasConfig';
import {CopyToDirOptions} from "@common/utils/copyFilesToDir";
import {modifyConfigYaml} from "#preload";
export {};

declare global {
  interface Window {
    __electron_preload__sha256sum: (data: BinaryLike) => string;
    __electron_preload__versions: string;
    __electron_preload__ipcRendererSend: (channel: string, ...args: any[]) => void;
    __electron_preload__ipcRendererOn: (
      channel: string,
      listener: (event: Electron.IpcRendererEvent, ...args: any[]) => void,
    ) => Electron.IpcRenderer;
    __electron_preload__getAlasConfig: () => AlasConfig;
    __electron_preload__checkIsNeedInstall: () => boolean;
    __electron_preload__modifyConfigYaml: (filePath: string, keyObj: {[k in string]: any}) => void;
    __electron_preload__copyFilesToDir: (
      pathList: string[],
      targetDirPath: string,
      options?: CopyToDirOptions | undefined,
    ) => Promise<void>;
  }
}
