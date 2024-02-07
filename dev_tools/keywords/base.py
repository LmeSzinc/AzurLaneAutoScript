import os
import re
import typing as t
from functools import cached_property

from module.base.code_generator import CodeGenerator
from module.config.utils import read_file
from module.logger import logger

UI_LANGUAGES = ['cn', 'cht', 'en', 'jp', 'es']


class TextMap:
    DATA_FOLDER = ''

    def __init__(self, lang: str):
        self.lang = lang

    def __contains__(self, name: t.Union[int, str]) -> bool:
        if isinstance(name, int) or (isinstance(name, str) and name.isdigit()):
            return int(name) in self.data
        return False

    @cached_property
    def data(self) -> dict[int, str]:
        if not os.path.exists(TextMap.DATA_FOLDER):
            logger.critical('`TextMap.DATA_FOLDER` does not exist, please set it to your path to StarRailData')
            exit(1)
        file = os.path.join(TextMap.DATA_FOLDER, 'TextMap', f'TextMap{self.lang.upper()}.json')
        data = {}
        for id_, text in read_file(file).items():
            text = text.replace('\u00A0', '')
            text = text.replace(r'{NICKNAME}', 'Trailblazer')
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


def text_to_variable(text):
    text = re.sub("'s |s' ", '_', text)
    text = re.sub(r'[ \-—:\'/•.]+', '_', text)
    text = re.sub(r'[(),#"?!&%*]|</?\w+>', '', text)
    # text = re.sub(r'[#_]?\d+(_times?)?', '', text)
    text = re.sub(r'<color=#?\w+>', '', text)
    text = text.replace('é', 'e')
    return text.strip('_')


def replace_templates(text: str) -> str:
    """
    Replace templates in data to make sure it equals to what is shown in game

    Examples:
        replace_templates("Complete Echo of War #4 time(s)")
        == "Complete Echo of War 1 time(s)"
    """
    text = re.sub(r'#4', '1', text)
    text = re.sub(r'</?\w+>', '', text)
    text = re.sub(r'<color=#?\w+>', '', text)
    text = re.sub(r'{.*?}', '', text)
    return text


class GenerateKeyword:
    text_map: dict[str, TextMap] = {lang: TextMap(lang) for lang in UI_LANGUAGES}
    text_map['cn'] = TextMap('chs')

    @staticmethod
    def read_file(file: str) -> dict:
        """
        Args:
            file: ./ExcelOutput/GameplayGuideData.json

        Returns:
            dict:
        """
        file = os.path.join(TextMap.DATA_FOLDER, file)
        return read_file(file)

    @classmethod
    def find_keyword(cls, keyword, lang) -> tuple[int, str]:
        """
        Args:
            keyword: text string or text id
            lang: Language to find

        Returns:
            text id (hash in TextMap)
            text
        """
        text_map = cls.text_map[lang]
        return text_map.find(keyword)

    output_file = ''

    def __init__(self):
        self.gen = CodeGenerator()
        self.keyword_class = self.__class__.__name__.removeprefix('Generate')
        self.keyword_index = 0
        self.keyword_format = {
            'id': 0,
            'name': 'Unnamed_Keyword'
        }
        for lang in UI_LANGUAGES:
            self.keyword_format[lang] = ''

    def gen_import(self):
        self.gen.Import(
            f"""
            from .classes import {self.keyword_class}
            """
        )

    def iter_keywords(self) -> t.Iterable[dict]:
        """
        Yields
            dict: {'text_id': 123456, 'any_attr': 1}
        """
        pass

    def convert_name(self, text: str, keyword: dict) -> str:
        return text_to_variable(text)

    def iter_rows(self) -> t.Iterable[dict]:
        for keyword in self.iter_keywords():
            keyword = self.format_keywords(keyword)
            yield keyword

    def format_keywords(self, keyword: dict) -> dict | None:
        base = self.keyword_format.copy()
        text_id = keyword.pop('text_id')
        if text_id is None:
            return
        # id
        self.keyword_index += 1
        base['id'] = self.keyword_index
        # Attrs
        base.update(keyword)
        # Name
        _, name = self.find_keyword(text_id, lang='en')
        name = self.convert_name(replace_templates(name), keyword=base)
        base['name'] = name
        # Translations
        for lang in UI_LANGUAGES:
            value = replace_templates(self.find_keyword(text_id, lang=lang)[1])
            base[lang] = value
        return base

    def generate(self):
        self.gen_import()
        self.gen.CommentAutoGenerage('dev_tools.keyword_extract')

        for keyword in self.iter_rows():
            with self.gen.Object(key=keyword['name'], object_class=self.keyword_class):
                for key, value in keyword.items():
                    self.gen.ObjectAttr(key, value)

        if self.output_file:
            print(f'Write {self.output_file}')
            self.gen.write(self.output_file)

    def __call__(self, *args, **kwargs):
        self.generate()
