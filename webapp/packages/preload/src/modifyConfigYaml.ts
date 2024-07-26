import {join, normalize} from 'path';
import {modifyYaml} from '@common/utils';
import {ALAS_CONFIG_YAML} from '@common/constant/config';

export function modifyConfigYaml(path: string, keyObj: {[k in string]: any}) {
  const configYamlPath = join(normalize(path) + `./config/${ALAS_CONFIG_YAML}`);
  return modifyYaml(configYamlPath, keyObj);
}
