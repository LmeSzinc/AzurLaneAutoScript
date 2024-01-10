import {execSync} from 'child_process';
import fs from 'fs';
import yaml from 'js-yaml';
import {join} from 'path';

import {name as appName, version} from '../package.json';
// @ts-ignore
import options from '../packages/main/electron-builder.config';

const dir = join(__dirname, '../release');

const appPath = `${dir}/mac/${options.productName}.app`;

const zipFileName = `${appName}_setup_${version}_mac.zip`;

const zipFilePath = `${dir}/${zipFileName}`;

const appBuilder = join(__dirname, '../node_modules/app-builder-bin/mac/app-builder');

console.log('Zipping...');

execSync(`ditto -c -k --sequesterRsrc --keepParent "${appPath}" "${zipFilePath}"`);

console.log('Finished zipping!');

console.log('Collect data...');

const blockmap = JSON.parse(
  execSync(`${appBuilder} blockmap -i ${zipFilePath} -o ${dir}/th.zip`).toString(),
);
console.log(blockmap);

// eslint-disable-next-line radix
blockmap.blockMapSize = parseInt(
  execSync(`ls -l ${dir}/th.zip | awk '{print $5}' && rm ${dir}/th.zip`).toString(),
);

const doc = yaml.load(fs.readFileSync(`${dir}/latest-mac.yml`, 'utf8')) as any;

doc.files.unshift({
  url: zipFileName,
  ...blockmap,
});

doc.path = zipFileName;
doc.sha512 = blockmap.sha512;

fs.writeFileSync(`${dir}/latest-mac.yml`, yaml.dump(doc, {lineWidth: 65535}), 'utf8');
