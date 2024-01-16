import type {Pair} from 'yaml';
import {parseDocument, visit} from 'yaml';
import fs from 'fs';
/**
 * Modify yaml file https://eemeli.org/yaml/#modifying-nodes
 * @param filePath
 * @param keyObj
 */
export function modifyYaml(filePath: string, keyObj: {[k in string]: never}) {
  try {
    const doc = parseDocument(fs.readFileSync(filePath, 'utf8'));
    const keysMap = new Map(Object.entries(keyObj));
    visit(doc, {
      Pair: (_node, pair: Pair) => {
        // @ts-ignore
        if (keysMap.has(pair?.key?.value)) {
          // @ts-ignore
          pair.value.value = keysMap.get(pair.key.value);
        }
      },
    });
    fs.writeFileSync(filePath, doc.toString(), 'utf8');
  } catch (e) {
    console.error(e);
  }
}
