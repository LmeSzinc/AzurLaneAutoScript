import type {Pair} from 'yaml';
import {parseDocument, visit} from 'yaml';
/**
 * Modify yaml file https://eemeli.org/yaml/#modifying-nodes
 * @param filePath
 * @param key
 * @param value
 */
export function modifyYaml(filePath: string, key: string, value: string) {
  try {
    const fs = require('fs');
    const doc = parseDocument(fs.readFileSync(filePath, 'utf8'));
    visit(doc, {
      Pair: (_node, pair: Pair<any, any>) => {
        if (pair?.key?.value === key) {
          pair.value.value = value;
        }
      },
    });
    fs.writeFileSync(filePath, doc.toString(), 'utf8');
  } catch (e) {
    console.error(e);
  }
}
