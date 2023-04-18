import {genMessage} from '../helper';

const modules = import.meta.glob('./ja-JP/**/*.ts');
export default {
  message: {
    ...genMessage(modules, 'ja-JP'),
  },
};
