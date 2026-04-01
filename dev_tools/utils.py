import os
import re

from tqdm import tqdm

from dev_tools.slpp import slpp


class LuaLoader:
    """
    Load decrypted scripts
    """

    server_alias = [
        ['zh-CN', 'zh-cn', 'cn', 'CN'],
        ['en-US', 'en-us', 'en', 'EN'],
        ['ja-JP', 'ja-jp', 'jp', 'JP'],
        ['zh-TW', 'zh-tw', 'tw', 'TW'],
        ['ko-KR', 'ko-kr', 'kr', 'KR'],
    ]

    def __init__(self, folder, server='zh-CN'):
        self.folder = folder
        self._server = ''
        self.server = server

    @property
    def server(self):
        return self._server

    @server.setter
    def server(self, value):
        self._server = self.get_alias(value)

    def get_alias(self, server):
        for alias_list in self.server_alias:
            if server in alias_list:
                for alias in alias_list:
                    folder = os.path.join(self.folder, alias)
                    if os.path.exists(folder) and os.path.isdir(folder):
                        return alias

        return server

    def filepath(self, path):
        return os.path.join(self.folder, self.server, path)

    def _load_file(self, file, keyword=None):
        """
        Args:
            file (str):

        Returns:
            dict:
        """
        with open(self.filepath(file), 'r', encoding='utf-8') as f:
            text = f.read()

        result = {}
        if text.startswith('_G'):
            text = '{' + text + '}'
            result = slpp.decode(text)
        else:
            if keyword:
                print(f'Finding keyword: {keyword}')
                pattern = rf"^{re.escape(keyword)}.*?\{{\s*\n(.*?)^\}}"
            else:
                pattern = r"\{\s*\n(.*?)^\}"
            m = re.search(pattern, text, re.S | re.M)
            if m:
                result = slpp.decode('{' + m.group(1) + '}')
        return result

    def load(self, path, keyword=None):
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
            result = self._load_file(path, keyword=keyword)

        print(f'{len(result.keys())} items loaded')
        return result


if __name__ == '__main__':
    # Use example
    lua = LuaLoader(r'xxx/AzurLaneData', server='en-US')
    res = lua.load('./sharecfg/item_data_statistics.lua')
