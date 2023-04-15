/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: 'class',
    content: [
        './packages/renderer/src/**/*.{vue,js,ts,jsx,tsx}',
    ],
    theme: {
        colors: {
            primary: '#C079F2',
            white: '#ffffff',
            neutral: '#C4C4C4',
            dark: '#2f3136',
            slate: '#020617',
        },
        extend: {},
    },
    plugins: [],
};
