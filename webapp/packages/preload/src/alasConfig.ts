import {alasPath, ThemeObj} from '../../main/src/config';
import {checkIsFirst} from '@common/utils/checkIsFirst';
const path = require('path');
const yaml = require('yaml');
const fs = require('fs');

let alasConfig: AlasConfig | null = null;
export async function getAlasConfig() {
  if (alasConfig === null) {
    const file = fs.readFileSync(path.join(alasPath, './config/deploy.yaml'), 'utf8');
    const config = yaml.parse(file) as DefAlasConfig;
    const WebuiPort = config.Deploy.Webui.WebuiPort.toString();
    const Theme = config.Deploy.Webui.Theme;
    alasConfig = {
      webuiUrl: `http://127.0.0.1:${WebuiPort}`,
      theme: ThemeObj[Theme] || 'light',
      language: config.Deploy.Webui.Language || 'en-US',
      repository: config.Deploy.Git.Repository,
    };
  }
  return alasConfig;
}

export function checkIsNeedInstall() {
  return checkIsFirst();
}
