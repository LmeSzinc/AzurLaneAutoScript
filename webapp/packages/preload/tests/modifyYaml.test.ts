import {test, expect} from 'vitest';
import {modifyYaml} from '../../common/utils/modifyYaml';
import getAlasABSPath from '../../common/utils/getAlasABSPath';
const path = require('path');
const fs = require('fs');
test('test write yaml', () => {
  const absPath = getAlasABSPath();
  const yamlPath = path.join(absPath, './config/deploy.yaml');
  modifyYaml(yamlPath, {Branch: 'dev'});
  const newYamlConfig1 = require('yaml').parse(fs.readFileSync(yamlPath, 'utf8'));
  expect(newYamlConfig1.Deploy.Git.Branch).toBe('dev');
  modifyYaml(yamlPath, {Branch: 'master'});
  const newYamlConfig2 = require('yaml').parse(fs.readFileSync(yamlPath, 'utf8'));
  expect(newYamlConfig2.Deploy.Git.Branch).toBe('master');
});
