import fsExtra from 'fs-extra';
import {join} from 'path';
import {
  AdbExecutableMap,
  ALAS_CONFIG_TEMPLATE_YAML,
  ALAS_CONFIG_YAML,
  GitExecutableMap,
  isMacOS,
  PythonExecutableMap,
  RepositoryMap,
} from '@alas/common';
import mustache from 'mustache';
import {app} from 'electron';
import {logger} from '@/core/Logger/customLogger';
import {getResources} from '@/utils/getResources';

/**
 * 校验配置文件是否存在  不存在则根据系统版本，语言环境进行创建
 * @param dirPath
 */
export function validateConfigFile(dirPath: string) {
  logger.info('validateConfigFile');
  const targetPath = join(dirPath, ALAS_CONFIG_YAML);
  const result = fsExtra.existsSync(targetPath);
  if (result) return true;
  /**
   * TODO 创建配置文件
   */
  fsExtra.ensureFileSync(targetPath);
  const resultTpl = fsExtra.existsSync(join(dirPath, ALAS_CONFIG_TEMPLATE_YAML));
  if (resultTpl) {
    fsExtra.copyFileSync(join(dirPath, ALAS_CONFIG_TEMPLATE_YAML), join(dirPath, ALAS_CONFIG_YAML));
    return true;
  }

  const tpl = fsExtra.readFileSync(getResources('deploy.yaml.tpl'), {
    encoding: 'utf-8',
  });
  logger.info('tpl create new deploy.yaml');
  const system = isMacOS ? 'macos' : 'windows';
  const localCode = app.getLocaleCountryCode().toLocaleLowerCase();
  let local: 'global' | 'china' = 'global';
  if (localCode === 'cn') {
    local = 'china';
  }
  const deployTpl = mustache.render(tpl, {
    repository: RepositoryMap[local],
    gitExecutable: GitExecutableMap[system],
    pythonExecutable: PythonExecutableMap[system],
    adbExecutable: AdbExecutableMap[system],
    language: local === 'china' ? 'zh-CN' : 'en-US',
    theme: 'default',
  });
  fsExtra.writeFileSync(targetPath, deployTpl, {encoding: 'utf-8'});
  return true;
}
