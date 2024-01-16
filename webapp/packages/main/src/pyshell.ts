import configInfo from '@/config';
import {logger} from '@/core/Logger/customLogger';
import {Options, PythonShell} from 'python-shell';
import treeKill from 'tree-kill';

const {alasPath, pythonPath} = configInfo;

export class PyShell extends PythonShell {
  constructor(script: string, args: Array<string> = []) {
    const options: Options = {
      mode: 'text',
      args: args,
      pythonPath: pythonPath,
      scriptPath: alasPath,
    };
    logger.info(`${pythonPath} ${script} ${args}`);
    super(script, options);
  }

  on(event: string, listener: (...args: any[]) => void): this {
    this.removeAllListeners(event);
    super.on(event, listener);
    return this;
  }

  killProcess(callback: (...args: any[]) => void) {
    treeKill(<number>this.childProcess.pid, 'SIGTERM', callback);
    return this;
  }
}
