import fs from 'fs';
import {join} from 'path';
import {ALAS_CONFIG_TEMPLATE_YAML, ALAS_CONFIG_TEST_TEMPLATE_YAML} from '@alas/common';
import {app} from 'electron';
import {getScriptRootPath} from '@/utils/getScriptRootPath';
export function checkIsFirst(): boolean {
  const absPath = getScriptRootPath('alas.py');
  debugger;
  return fs.existsSync(
    join(
      absPath,
      `/config/${!app.isPackaged ? ALAS_CONFIG_TEST_TEMPLATE_YAML : ALAS_CONFIG_TEMPLATE_YAML}`,
    ),
  );
}
