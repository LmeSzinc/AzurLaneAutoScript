import {webuiTheme, webuiUrl,language} from '../../main/src/config';


export interface AlasConfig {
    webuiUrl: string;
    theme: 'light' | 'dark' | 'system';
    language: DefAlasConfig['Deploy']['Webui']['Language'];
}


export function getAlasConfig(): AlasConfig {
    return {
        webuiUrl,
        theme: webuiTheme,
        language,
    };
}
