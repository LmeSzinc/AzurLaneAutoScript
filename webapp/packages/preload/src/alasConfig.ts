import {webuiTheme, webuiUrl, language, repository} from '../../main/src/config';

export interface AlasConfig {
  webuiUrl: string;
  theme: 'light' | 'dark' | 'system';
  language: DefAlasConfig['Deploy']['Webui']['Language'];
  repository: DefAlasConfig['Deploy']['Git']['Repository'];
}

export function getAlasConfig(): AlasConfig {
  return {
    webuiUrl,
    theme: webuiTheme,
    language,
    repository,
  };
}
