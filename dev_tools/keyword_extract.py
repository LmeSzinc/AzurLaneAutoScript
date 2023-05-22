import os
import typing as t
from functools import cached_property

from module.base.code_generator import CodeGenerator
from module.config.utils import read_file
from module.logger import logger
from module.ocr.keyword import text_to_variable

UI_LANGUAGES = ['cn', 'cht', 'en', 'jp']


class TextMap:
    DATA_FOLDER = ''

    def __init__(self, lang: str):
        self.lang = lang

    @cached_property
    def data(self) -> dict[int, str]:
        if not TextMap.DATA_FOLDER:
            logger.critical('`TextMap.DATA_FOLDER` is empty, please set it to your path to StarRailData')
            exit(1)
        file = os.path.join(TextMap.DATA_FOLDER, 'TextMap', f'TextMap{self.lang.upper()}.json')
        data = {}
        for id_, text in read_file(file).items():
            data[int(id_)] = text
        return data

    def find(self, name: t.Union[int, str]) -> tuple[int, str]:
        """
        Args:
            name:

        Returns:
            text id (hash in TextMap)
            text
        """
        if isinstance(name, int) or (isinstance(name, str) and name.isdigit()):
            name = int(name)
            try:
                return name, self.data[name]
            except KeyError:
                pass

        name = str(name)
        for row_id, row_name in self.data.items():
            if row_id >= 0 and row_name == name:
                return row_id, row_name
        for row_id, row_name in self.data.items():
            if row_name == name:
                return row_id, row_name
        logger.error(f'Cannot find name: "{name}" in language {self.lang}')
        return 0, ''


class KeywordExtract:
    def __init__(self):
        self.text_map: dict[str, TextMap] = {lang: TextMap(lang) for lang in UI_LANGUAGES}
        self.keywords_id: list[int] = []

    def find_keyword(self, keyword, lang):
        text_map = self.text_map[lang]
        return text_map.find(keyword)

    def load_keywords(self, keywords: list[str], lang='cn'):
        text_map = self.text_map[lang]
        self.keywords_id = [text_map.find(keyword)[0] for keyword in keywords]
        self.keywords_id = [keyword for keyword in self.keywords_id if keyword != 0]

    def write_keywords(
            self,
            keyword_class,
            output_file: str
    ):
        """
        Args:
            keyword_class:
            keyword_import:
            output_file:
        """
        gen = CodeGenerator()
        gen.Import(f"""
        from .classes import {keyword_class}
        """)
        gen.CommentAutoGenerage('dev_tools.keyword_extract')
        for index, keyword in enumerate(self.keywords_id):
            _, en = self.find_keyword(keyword, lang='en')
            en = text_to_variable(en)
            with gen.Object(key=en, object_class=keyword_class):
                gen.ObjectAttr(key='id', value=index + 1)
                for lang in UI_LANGUAGES:
                    gen.ObjectAttr(key=lang, value=self.find_keyword(keyword, lang=lang)[1])

        gen.write(output_file)


def generate():
    ex = KeywordExtract()
    ex.load_keywords(['模拟宇宙', '拟造花萼（金）', '拟造花萼（赤）', '凝滞虚影', '侵蚀隧洞', '忘却之庭'])
    ex.write_keywords(keyword_class='DungeonNav', output_file='./tasks/dungeon/keywords/nav.py')
    ex.load_keywords(['行动摘要', '生存索引', '每日实训'])
    ex.write_keywords(keyword_class='DungeonTab', output_file='./tasks/dungeon/keywords/tab.py')


if __name__ == '__main__':
    TextMap.DATA_FOLDER = r''
    generate()
