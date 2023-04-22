import type {OptionItem} from '/#/config';

export const repositoryMap = {
  global: 'https://e.coding.net/llop18870/alas/AzurLaneAutoScript.git',
  china: 'https://github.com/LmeSzinc/AzurLaneAutoScript',
};

export const repositoryValueMap = {
  [repositoryMap.global]: 'global',
  [repositoryMap.china]: 'china',
};

export const repositoryList: OptionItem[] = [
  {
    value: repositoryMap.china,
    label: '中国大陆',
  },
  {
    value: repositoryMap.global,
    label: '全球',
  },
];
