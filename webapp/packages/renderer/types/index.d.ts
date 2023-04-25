import type {BinaryLike} from 'node:crypto';
import type {AlasConfig} from '../../preload/src/alasConfig';
import type {ThemeVal} from '/#/config';
import {checkIsNeedInstall} from '../../preload/src/alasConfig';

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
  }
}
