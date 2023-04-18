 import { genMessage } from '../helper';

const modules = import.meta.glob('./en-US/**/*.ts');
export default {
  message: {
    ...genMessage(modules, 'en-US'),
  },
};
