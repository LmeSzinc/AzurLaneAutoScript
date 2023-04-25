import type {CallbackFun} from '/@/coreService';
import getAlasABSPath from '@common/utils/getAlasABSPath';

export const createAlasConfigCache: CallbackFun = async (ctx, next) => {
  const {} = ctx;

  const config = {};
  const alasPath = getAlasABSPath();

  console.log({config});
};
