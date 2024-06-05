/** @type {import('vls').VeturConfig} */
module.exports = {
  settings: {
    'vetur.useWorkspaceDependencies': true,
    'vetur.experimental.templateInterpolationService': true,
  },
  projects: [
    {
      root: './packages/renderer',
      tsconfig: './tsconfig.json',
      snippetFolder: './.vscode/vetur/snippets',
<<<<<<< HEAD
      globalComponents: ['./src/components/**/*.vue'],
=======
      globalComponents: [
        './src/components/**/*.vue',
      ],
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
    },
    {
      root: './packages/main',
      tsconfig: './tsconfig.json',
    },
    {
      root: './packages/preload',
      tsconfig: './tsconfig.json',
    },
  ],
};
