import {alasPath, pythonPath} from '/@/config';

const {PythonShell} = require('python-shell');
const treeKill = require('tree-kill');


export class PyShell extends PythonShell {
  constructor(script: string, args: Array<string> = []) {
    const options = {
      mode: 'text',
      args: args,
      pythonPath: pythonPath,
      scriptPath: alasPath,
    };
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
