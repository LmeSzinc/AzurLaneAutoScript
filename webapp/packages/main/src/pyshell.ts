import {alasPath, pythonPath} from '/@/config';
<<<<<<< HEAD
import logger from '/@/logger';
=======
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0

const {PythonShell} = require('python-shell');
const treeKill = require('tree-kill');

<<<<<<< HEAD
=======

>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
export class PyShell extends PythonShell {
  constructor(script: string, args: Array<string> = []) {
    const options = {
      mode: 'text',
      args: args,
      pythonPath: pythonPath,
      scriptPath: alasPath,
    };
<<<<<<< HEAD
    logger.info(`${pythonPath} ${script} ${args}`);
=======
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
    super(script, options);
  }

  on(event: string, listener: (...args: any[]) => void): this {
    this.removeAllListeners(event);
    super.on(event, listener);
    return this;
  }

  kill(callback: (...args: any[]) => void): this {
    treeKill(this.childProcess.pid, 'SIGTERM', callback);
    return this;
  }
}
