#!/usr/bin/node
const {build} = require('vite');
const {dirname} = require('path');

/** @type 'production' | 'development' | 'test' */
<<<<<<< HEAD
const mode = (process.env.MODE = process.env.MODE || 'production');
=======
const mode = process.env.MODE = process.env.MODE || 'production';
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0

const packagesConfigs = [
  'packages/main/vite.config.js',
  'packages/preload/vite.config.js',
  'packages/renderer/vite.config.js',
];

<<<<<<< HEAD
/**
 * Run `vite build` for config file
 */
const buildByConfig = configFile => build({configFile, mode});
=======

/**
 * Run `vite build` for config file
 */
const buildByConfig = (configFile) => build({configFile, mode});
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
(async () => {
  try {
    const totalTimeLabel = 'Total bundling time';
    console.time(totalTimeLabel);

    for (const packageConfigPath of packagesConfigs) {
<<<<<<< HEAD
=======

>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
      const consoleGroupName = `${dirname(packageConfigPath)}/`;
      console.group(consoleGroupName);

      const timeLabel = 'Bundling time';
      console.time(timeLabel);

      await buildByConfig(packageConfigPath);

      console.timeEnd(timeLabel);
      console.groupEnd();
      console.log('\n'); // Just for pretty print
    }
    console.timeEnd(totalTimeLabel);
  } catch (e) {
    console.error(e);
    process.exit(1);
  }
})();
