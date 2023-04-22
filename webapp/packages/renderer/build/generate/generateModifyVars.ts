import {generateAntColors, primaryColor} from '../config/themeConfig';
import {getThemeVariables} from 'ant-design-vue/dist/theme';
import {resolve} from 'path';

/**
 * less global variable
 */
export function generateModifyVars(dark = false) {
  const palettes = generateAntColors(primaryColor);
  const primary = palettes[5];
  const primaryColorObj: Record<string, string> = {};

  for (let index = 0; index < 10; index++) {
    primaryColorObj[`primary-${index + 1}`] = palettes[index];
  }

  const modifyVars = getThemeVariables({dark});
  return {
    ...modifyVars,
    // Used for global import to avoid the need to import each style file separately
    // reference:  Avoid repeated references
    hack: `${modifyVars.hack} @import (reference) "${resolve(
      'packages/renderer/src/design/config.less',
    )}";`,
    'primary-color': primary,
    ...primaryColorObj,
  };
}
