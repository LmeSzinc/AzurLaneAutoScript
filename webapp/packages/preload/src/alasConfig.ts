import {ALAS_CONFIG_YAML} from '@common/constant/config';
import {getAlasABSPath, checkIsFirst} from '@common/utils';
import {ThemeObj} from '@common/constant/theme';
import {Dirent} from 'fs';
const path = require('path');
const yaml = require('yaml');
const fs = require('fs');

let alasConfig: AlasConfig | null = null;
export async function getAlasConfig() {
  if (alasConfig === null) {
    const alasPath = getAlasABSPath();
    const file = fs.readFileSync(path.join(alasPath, `./config/${ALAS_CONFIG_YAML}`), 'utf8');
    const config = yaml.parse(file) as DefAlasConfig;
    const WebuiPort = config.Deploy.Webui.WebuiPort.toString();
    const Theme = config.Deploy.Webui.Theme;
    alasConfig = {
      webuiUrl: `http://127.0.0.1:${WebuiPort}`,
      theme: ThemeObj[Theme] || 'light',
      language: config.Deploy.Webui.Language || 'en-US',
      repository: config.Deploy.Git.Repository as any,
      alasPath,
    };
  }
  return alasConfig;
}

export function checkIsNeedInstall() {
  return checkIsFirst();
}

interface fileInfoItem {
  name: string;
  path: string;
  lastModifyTime: Date;
}
export function getAlasConfigDirFiles() {
  const alasPath = getAlasABSPath();
  const configPath = path.join(alasPath, `./config`);
  const files: Dirent[] = fs.readdirSync(configPath, {withFileTypes: true});
  const filesInfoList: fileInfoItem[] = files.map((file: Dirent) => {
    const name = file.name;
    const filePath = path.join(configPath, name);
    return {
      name,
      path: filePath,
      lastModifyTime: getFileUpdateDate(filePath),
    };
  });
  return {
    configPath,
    files: filesInfoList,
  };
}

export function getFileUpdateDate(path: string) {
  const stat = fs.statSync(path);
  return stat.mtime;
}
