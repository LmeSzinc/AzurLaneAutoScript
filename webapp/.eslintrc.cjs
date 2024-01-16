/* eslint-env node */
require('@rushstack/eslint-patch/modern-module-resolution');

module.exports = {
  'root': true,
  'env': {
    'es2021': true,
    'node': true,
    'browser': false,
  },
  extends: [
    'eslint:recommended',
    /** @see https://github.com/typescript-eslint/typescript-eslint/tree/master/packages/eslint-plugin#recommended-configs */
    // 'plugin:@typescript-eslint/recommended',
    'prettier',
    'plugin:prettier/recommended',
    '@electron-toolkit',
    '@electron-toolkit/eslint-config-ts/eslint-recommended',
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    'ecmaVersion': 12,
    'sourceType': 'module',
  },
  // plugins: ['@typescript-eslint'],
  ignorePatterns: ['node_modules/**', '**/dist/**','release/**'],
  rules: {
    'vue/require-default-prop': 'off',
    'vue/multi-word-component-names': 'off',
    // '@typescript-eslint/no-unused-vars': [
    //   'error',
    //   {
    //     'argsIgnorePattern': '^_',
    //     'varsIgnorePattern': '^_',
    //   },
    // ],
    '@typescript-eslint/ban-ts-comment': 'off',
    '@typescript-eslint/no-var-requires': 'off',
    '@typescript-eslint/consistent-type-imports': 'off',


    // ESLint: Definition for rule '@typescript-eslint/consistent-type-imports' was not found.(@typescript-eslint/consistent-type-imports)
    // ESLint: Definition for rule '@typescript-eslint/no-empty-function' was not found.(@typescript-eslint/no-empty-function)
    // ESLint: Definition for rule '@typescript-eslint/no-empty-interface' was not found.(@typescript-eslint/no-empty-interface)
    // ESLint: Definition for rule '@typescript-eslint/no-unused-vars' was not found.(@typescript-eslint/no-unused-vars)
    '@typescript-eslint/no-empty-function': 'off',
    '@typescript-eslint/no-empty-interface': 'off',
    '@typescript-eslint/no-unused-vars': 'off',
    /**
     * Having a semicolon helps the optimizer interpret your code correctly.
     * This avoids rare errors in optimized code.
     * @see https://twitter.com/alex_kozack/status/1364210394328408066
     */
    'semi': ['error', 'always'],
    /**
     * This will make the history of changes in the hit a little cleaner
     */
    'comma-dangle': ['warn', 'always-multiline'],
    /**
     * Just for beauty
     */
    'quotes': [
      'warn',
      'single',
      {
        'avoidEscape': true,
      },
    ],
    '@typescript-eslint/no-explicit-any': 'off',
    '@typescript-eslint/ban-types': 'off',
    '@typescript-eslint/explicit-function-return-type': 'off',
    'no-unused-vars': 'off',
    },
};
