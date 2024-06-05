import getAlasABSPath from './getAlasABSPath';
import fs from 'fs';
import {join} from 'path';
import {ALAS_CONFIG_TEMPLATE_YAML, ALAS_CONFIG_TEST_TEMPLATE_YAML} from '../constant/config';
export function checkIsFirst(): boolean {
  const absPath = getAlasABSPath();
  return fs.existsSync(
    join(
      absPath,
      `/config/${import.meta.env.DEV ? ALAS_CONFIG_TEST_TEMPLATE_YAML : ALAS_CONFIG_TEMPLATE_YAML}`,
    ),
  );
}
