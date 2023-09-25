// uno.config.ts
import {
  defineConfig,
  presetAttributify,
  presetIcons,
  presetTypography,
  presetUno,
  presetWebFonts,
  transformerDirectives,
  transformerVariantGroup,
} from 'unocss';
import {primaryColor} from './build/config/themeConfig';

export default defineConfig({
  theme: {
    colors: {
      primary: primaryColor,
      white: '#ffffff',
      neutral: '#C4C4C4',
      dark: '#2f3136',
      slate: '#020617',
    },
  },
  presets: [presetUno(), presetAttributify(), presetIcons(), presetTypography(), presetWebFonts()],
  transformers: [transformerDirectives(), transformerVariantGroup()],
});
