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
      globalComponents: [
        './src/components/**/*.vue',
      ],
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
