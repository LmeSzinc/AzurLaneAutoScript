import getAlasABSPath from './getAlasABSPath';
import fs from 'fs';
import {join} from 'path';
export function checkIsFirst(): boolean {
  const absPath = getAlasABSPath();
  return fs.existsSync(join(absPath + '/config/deploy.template.yaml'));
}
