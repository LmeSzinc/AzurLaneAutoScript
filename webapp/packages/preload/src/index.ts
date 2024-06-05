<<<<<<< HEAD
/**
 * @module preload
 */

export {sha256sum} from './nodeCrypto';
export {versions} from './versions';
export {ipcRendererSend, ipcRendererOn} from './electronApi';
export {getAlasConfig, checkIsNeedInstall, getAlasConfigDirFiles} from './alasConfig';
export {copyFilesToDir} from '@common/utils/copyFilesToDir';
export {modifyConfigYaml} from './modifyConfigYaml';
=======
import {contextBridge} from 'electron';

const apiKey = 'electron';
/**
 * @see https://github.com/electron/electron/issues/21437#issuecomment-573522360
 */
const api: ElectronApi = {
  versions: process.versions,
};

/**
 * The "Main World" is the JavaScript context that your main renderer code runs in.
 * By default, the page you load in your renderer executes code in this world.
 *
 * @see https://www.electronjs.org/docs/api/context-bridge
 */
contextBridge.exposeInMainWorld(apiKey, api);
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
