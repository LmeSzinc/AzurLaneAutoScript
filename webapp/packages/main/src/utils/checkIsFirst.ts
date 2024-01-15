import fs from 'fs';
import {join} from 'path';
import {ALAS_CONFIG_TEMPLATE_YAML, ALAS_CONFIG_TEST_TEMPLATE_YAML} from '@alas/common';
import {app} from 'electron';
import {getScriptRootPath} from '@/utils/getScriptRootPath';
export function checkIsFirst(): boolean {
  const absPath = getScriptRootPath('alas.py');
  return fs.existsSync(
    /**
     *  如果是开发环境，那么就是 deploy.test.template.yaml 通过是否打包来区分
     *  在初始包下载完成后，config中只会存在 deploy.yaml 文件
     */
    join(
      absPath,
      `/config/${!app.isPackaged ? ALAS_CONFIG_TEST_TEMPLATE_YAML : ALAS_CONFIG_TEMPLATE_YAML}`,
    ),
  );
}
