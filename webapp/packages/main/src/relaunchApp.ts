import {app} from 'electron';
import {ALAS_RELAUNCH_ARGV} from '@common/constant/config';

export const isRelaunch = process.argv.includes(ALAS_RELAUNCH_ARGV);

function relaunchApp() {
  /**
   * TODO Some events need to be rehandled for restart operations
   */
  if (!isRelaunch) {
    app.relaunch({args: process.argv.slice(1).concat([ALAS_RELAUNCH_ARGV])});
  }
}

export default relaunchApp;
