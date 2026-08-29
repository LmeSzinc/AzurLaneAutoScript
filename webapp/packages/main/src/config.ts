const yaml = require('yaml');
const fs = require('fs');
const path = require('path');

// export const alasPath = 'D:/AzurLaneAutoScript';
function findAlasPath() {
  const roots = [
    process.cwd(),
    __dirname,
    process.execPath,
  ];
  const configFiles = ['./config/deploy.yaml'];

  for (const root of roots) {
    let current = fs.statSync(root).isDirectory() ? root : path.dirname(root);
    let searching = true;
    while (searching) {
      for (const configFile of configFiles) {
        if (fs.existsSync(path.join(current, configFile))) {
          return current;
        }
      }

      const parent = path.dirname(current);
      if (parent === current) {
        searching = false;
      } else {
        current = parent;
      }
    }
  }

  return process.cwd();
}

export const alasPath = findAlasPath();

const file = fs.readFileSync(path.join(alasPath, './config/deploy.yaml'), 'utf8');
const config = yaml.parse(file);
const PythonExecutable = config.Deploy.Python.PythonExecutable;
const WebuiPort = config.Deploy.Webui.WebuiPort.toString();

function resolvePath(filePath: string) {
  return path.isAbsolute(filePath) ? filePath : path.join(alasPath, filePath);
}

function findMacArmCondaPython() {
  if (process.platform !== 'darwin' || process.arch !== 'arm64') {
    return null;
  }

  const home = process.env.HOME;
  const envPaths = [
    path.join(alasPath, 'alas'),
    path.join(alasPath, 'envs', 'alas'),
    path.join(alasPath, '.conda', 'envs', 'alas'),
    home ? path.join(home, '.conda', 'envs', 'alas') : null,
    home ? path.join(home, 'miniconda3', 'envs', 'alas') : null,
    home ? path.join(home, 'miniforge3', 'envs', 'alas') : null,
    home ? path.join(home, 'anaconda3', 'envs', 'alas') : null,
    '/opt/homebrew/Caskroom/miniconda/base/envs/alas',
    '/opt/homebrew/Caskroom/miniforge/base/envs/alas',
  ];

  for (const envPath of envPaths) {
    if (!envPath) {
      continue;
    }
    const python = path.join(envPath, 'bin', 'python');
    if (fs.existsSync(python)) {
      return python;
    }
  }

  return null;
}

function resolvePythonPath() {
  const configuredPython = resolvePath(PythonExecutable);
  if (fs.existsSync(configuredPython)) {
    return configuredPython;
  }

  return findMacArmCondaPython() || configuredPython;
}

export const pythonPath = resolvePythonPath();
export const webuiUrl = `http://127.0.0.1:${WebuiPort}`;
export const webuiPath = 'gui.py';
export const webuiArgs = ['--port', WebuiPort, '--electron'];
export const dpiScaling = Boolean(config.Deploy.Webui.DpiScaling) || (config.Deploy.Webui.DpiScaling === undefined) ;
