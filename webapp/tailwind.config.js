/** @type {import('tailwindcss').Config} */
const {primaryColor} = require('./packages/renderer/build/config/themeConfig');
module.exports = {
  darkMode: 'class',
  content: ['./packages/renderer/src/**/*.{vue,js,ts,jsx,tsx}'],

  theme: {
    extend: {
      colors: {
        primary: primaryColor,
        white: '#ffffff',
        neutral: '#C4C4C4',
        dark: '#2f3136',
        slate: '#020617',
      },
      maxWidth: {
        '1/3': '33.333333%',
      },
    },
  },
  plugins: [createEnterPlugin()],
};

/**
 * Used for animation when the element is displayed
 * @param maxOutput The larger the maxOutput output, the larger the generated css volume
 */
function createEnterPlugin(maxOutput = 6) {
  const createCss = (index, d = 'x') => {
    const upd = d.toUpperCase();
    return {
      [`*> .enter-${d}:nth-child(${index})`]: {
        transform: `translate${upd}(50px)`,
      },
      [`*> .-enter-${d}:nth-child(${index})`]: {
        transform: `translate${upd}(-50px)`,
      },
      [`* > .enter-${d}:nth-child(${index}),* > .-enter-${d}:nth-child(${index})`]: {
        'z-index': `${10 - index}`,
        opacity: '0',
        animation: `enter-${d}-animation 0.4s ease-in-out 0.3s`,
        'animation-fill-mode': 'forwards',
        'animation-delay': `${(index * 1) / 10}s`,
      },
    };
  };
  const handler = ({addBase}) => {
    const addRawCss = {};
    for (let index = 1; index < maxOutput; index++) {
      Object.assign(addRawCss, {
        ...createCss(index, 'x'),
        ...createCss(index, 'y'),
      });
    }
    addBase({
      ...addRawCss,
      [`@keyframes enter-x-animation`]: {
        to: {
          opacity: '1',
          transform: 'translateX(0)',
        },
      },
      [`@keyframes enter-y-animation`]: {
        to: {
          opacity: '1',
          transform: 'translateY(0)',
        },
      },
    });
  };
  return {handler};
}
