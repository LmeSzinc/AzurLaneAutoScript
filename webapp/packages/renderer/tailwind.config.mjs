import tailwindcssConfig from '../../tailwind.config.js';

/** @type {import('tailwindcss').Config} */
export default {
    ...tailwindcssConfig,
      content: [
        './src/**/*.{vue,js,ts,jsx,tsx}',
    ],
};

