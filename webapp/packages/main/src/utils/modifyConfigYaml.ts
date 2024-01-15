import {join, normalize} from 'path';
import {modifyYaml} from './modifyYaml';
import {ALAS_CONFIG_YAML} from '@alas/common';

export function modifyConfigYaml(path: string, keyObj: {[k in string]: never}) {
  const configYamlPath = join(normalize(path) + `./config/${ALAS_CONFIG_YAML}`);
  return modifyYaml(configYamlPath, keyObj);
}
