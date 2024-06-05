if (process.env.VITE_APP_VERSION === undefined) {
<<<<<<< HEAD
  const now = new Date();
  process.env.VITE_APP_VERSION = `${now.getUTCFullYear() - 2000}.${
    now.getUTCMonth() + 1
  }.${now.getUTCDate()}-${now.getUTCHours() * 60 + now.getUTCMinutes()}`;
=======
  const now = new Date;
  process.env.VITE_APP_VERSION = `${now.getUTCFullYear() - 2000}.${now.getUTCMonth() + 1}.${now.getUTCDate()}-${now.getUTCHours() * 60 + now.getUTCMinutes()}`;
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
}

/**
 * @type {import('electron-builder').Configuration}
 * @see https://www.electron.build/configuration/configuration
 */
const config = {
  directories: {
    output: 'dist',
    buildResources: 'buildResources',
  },
<<<<<<< HEAD
  files: ['packages/**/dist/**'],
=======
  files: [
    'packages/**/dist/**',
  ],
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
  extraMetadata: {
    version: process.env.VITE_APP_VERSION,
  },
};

module.exports = config;
