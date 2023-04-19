import {app} from 'electron';
import {isMacintosh} from './utils/env';

export const isRelaunch = process.argv.includes('relaunch');

function relaunchApp() {
  if (!isRelaunch) {
    app.relaunch({args: ['relaunch']});
    isMacintosh ? app.quit() : app.exit(0);
  }
}

export default relaunchApp;
