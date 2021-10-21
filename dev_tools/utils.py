import os
import re

from tqdm import tqdm
from dev_tools.slpp import slpp


class LuaLoader:
    """
    Load decrypted scripts
    """

    def __init__(self, folder, server='zh-CN'):
        self.folder = folder
        self.server = server

    def filepath(self, path):
        return os.path.join(self.folder, self.server, path)

    def _load_file(self, file):
        """
        Args:
            file (str):

        Returns:
            dict:
        """
        with open(self.filepath(file), 'r', encoding='utf-8') as f:
            text = f.read()

        result = {}
        matched = re.findall('function \(\)(.*?)end[()]', text, re.S)
        if matched:
            # Most files are in this format
            """
            pg = pg or {}
            slot0 = pg
            slot0.chapter_template = {}
            
            (function ()
                ...
            end)()
            """
            for func in matched:
                add = slpp.decode('{' + func + '}')
                result.update(add)
        elif text.startswith('pg'):
            # Old format
            """
            pg = pg or {}
            pg.item_data_statistics = {
                ...
            }
            """
            # or
            """
            pg = pg or {}

            rawset(pg, "item_data_statistics", rawget(pg, "item_data_statistics") or {
                ...
            }
            """
            text = '{' + text.split('{', 2)[2]
            result = slpp.decode(text)
        else:
            # Another format, just bare data
            """
            _G.pg.expedition_data_template[...] = {
                ...
            }
            _G.pg.expedition_data_template[...] = {
                ...
            }
            ...
            """
            text = '{' + text + '}'
            result = slpp.decode(text)

        return result

    def load(self, path):
        """
        Load a lua file to python dictionary, handling the differences

        Args:
            path (str): Relavice path from {folder}/{server}.
                Can be a file or a directory

        Returns:
            dict:
        """
        print(f'Loading {path}')
        if os.path.isdir(self.filepath(path)):
            result = {}
            for file in tqdm(os.listdir(self.filepath(path))):
                result.update(self._load_file(f'./{path}/{file}'))
        else:
            result = self._load_file(path)

        print(f'{len(result.keys())} items loaded')
        return result


if __name__ == '__main__':
    # Use example
    lua = LuaLoader(r'xxx/AzurLaneData', server='en-US')
    res = lua.load('./sharecfg/item_data_statistics.lua')
