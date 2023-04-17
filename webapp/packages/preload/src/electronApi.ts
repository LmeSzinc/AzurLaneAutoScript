import {ipcRenderer} from 'electron';
import IpcRenderer = Electron.IpcRenderer;

export function ipcRendererSend(channel: string, ...args: any[]): void {
    ipcRenderer.send(channel, ...args);
}

export function ipcRendererOn(channel: string, listener: (event: Electron.IpcRendererEvent, ...args: any[]) => void): IpcRenderer {
    return ipcRenderer.on(channel, listener);
}
