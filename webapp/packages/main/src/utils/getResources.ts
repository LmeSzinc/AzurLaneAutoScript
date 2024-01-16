import {app} from 'electron';
import {join} from 'path';

export function getResources(name: string) {
  return app.isPackaged
    ? join(app.getAppPath(), '../../resources/icon.png')
    : join(app.getAppPath(), '../icon.png');
}
