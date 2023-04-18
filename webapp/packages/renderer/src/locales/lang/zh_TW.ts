import {genMessage} from '../helper';

const modules = import.meta.glob('./zh-TW/**/*.ts');
export default {
  message: {
    ...genMessage(modules, 'zh-TW'),
  },
};
