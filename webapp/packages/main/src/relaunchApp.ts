import {app} from 'electron';
import {isMacintosh} from '@common/utils/env';

export const isRelaunch = process.argv.includes('relaunch');

function relaunchApp() {
  /**
   * TODO Some events need to be rehandled for restart operations
   */
  if (!isRelaunch) {
    app.relaunch({args: ['relaunch']});
    isMacintosh ? app.quit() : app.exit(0);
  }
}

export default relaunchApp;
