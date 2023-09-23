export const ALAS_CONFIG_YAML = 'deploy.yaml';
export const ALAS_CONFIG_TEMPLATE_YAML = 'deploy.template.yaml';
export const ALAS_CONFIG_TEST_TEMPLATE_YAML = 'deploy.test.template.yaml';
export const ALAS_INSTR_FILE = 'installer.py';
export const ALAS_RELAUNCH_ARGV = '--relaunch';

export const RepositoryMap = {
  china: 'cn',
  global: 'global',
};

export const GitExecutableMap = {
  windows: './toolkit/Git/mingw64/bin/git.exe',
  macos: '/usr/bin/git',
  linux: '/usr/bin/git',
};

export const AdbExecutableMap = {
  windows: './toolkit/Lib/site-packages/adbutils/binaries/adb.exe',
  macos: '/usr/bin/adb',
  linux: '/usr/bin/adb',
};

export const PythonExecutableMap = {
  windows: './toolkit/python.exe',
  macos: '/usr/bin/python',
  linux: '/usr/bin/python',
};
