import type {OptionItem} from '/#/config';

export const repositoryMap = {
  china: 'cn',
  global: 'global',
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
