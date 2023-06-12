import os
import re
import typing as t
from functools import cached_property

from module.base.code_generator import CodeGenerator
from module.config.utils import deep_get, read_file
from module.logger import logger

UI_LANGUAGES = ['cn', 'cht', 'en', 'jp']


def text_to_variable(text):
    text = re.sub("'s |s' ", '_', text)
    text = re.sub('[ \-—:\']+', '_', text)
    text = re.sub(r'[(),#]|</?\w+>', '', text)
    # text = re.sub(r'[#_]?\d+(_times?)?', '', text)
    return text


def dungeon_name(name: str) -> str:
    name = text_to_variable(name)
    name = re.sub('Bud_of_(Memories|Aether|Treasures)', r'Calyx_Golden_\1', name)
    name = re.sub('Bud_of_(.*)', r'Calyx_Crimson_\1', name)
    name = re.sub('Shape_of_(.*)', r'Stagnant_Shadow_\1', name)
    if name in ['Destructions_Beginning', 'End_of_the_Eternal_Freeze']:
        name = 'Echo_of_War_' + name
    return name


class TextMap:
    DATA_FOLDER = ''

    def __init__(self, lang: str):
        self.lang = lang

    @cached_property
    def data(self) -> dict[int, str]:
        if not os.path.exists(TextMap.DATA_FOLDER):
            logger.critical('`TextMap.DATA_FOLDER` does not exist, please set it to your path to StarRailData')
            exit(1)
        file = os.path.join(TextMap.DATA_FOLDER, 'TextMap', f'TextMap{self.lang.upper()}.json')
        data = {}
        for id_, text in read_file(file).items():
            text = text.replace('\u00A0', '')
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


def replace_templates(text: str) -> str:
    """
    Replace templates in data to make sure it equals to what is shown in game

    Examples:
        replace_templates("Complete Echo of War #4 time(s)")
        == "Complete Echo of War 1 time(s)"
    """
    text = re.sub(r'#4', '1', text)
    text = re.sub(r'</?\w+>', '', text)
    return text


class KeywordExtract:
    def __init__(self):
        self.text_map: dict[str, TextMap] = {lang: TextMap(lang) for lang in UI_LANGUAGES}
        self.keywords_id: list[int] = []

    def iter_guide(self) -> t.Iterable[int]:
        file = os.path.join(TextMap.DATA_FOLDER, './ExcelOutput/GameplayGuideData.json')
        for data in read_file(file).values():
            hash_ = deep_get(data, keys='Name.Hash')
            _, name = self.find_keyword(hash_, lang='cn')
            if '忘却之庭' in name or '遗秘' in name:
                continue
            yield hash_

    def find_keyword(self, keyword, lang) -> tuple[int, str]:
        """
        Args:
            keyword: text string or text id
            lang: Language to find

        Returns:
            text id (hash in TextMap)
            text
        """
        text_map = self.text_map[lang]
        return text_map.find(keyword)

    def load_keywords(self, keywords: list[str | int], lang='cn'):
        text_map = self.text_map[lang]
        self.keywords_id = [text_map.find(keyword)[0] for keyword in keywords]
        self.keywords_id = [keyword for keyword in self.keywords_id if keyword != 0]

    def write_keywords(
            self,
            keyword_class,
            output_file: str,
            text_convert=text_to_variable,
    ):
        """
        Args:
            keyword_class:
            output_file:
            text_convert:
        """
        gen = CodeGenerator()
        gen.Import(f"""
        from .classes import {keyword_class}
        """)
        gen.CommentAutoGenerage('dev_tools.keyword_extract')
        for index, keyword in enumerate(self.keywords_id):
            _, name = self.find_keyword(keyword, lang='en')
            name = text_convert(replace_templates(name))
            with gen.Object(key=name, object_class=keyword_class):
                gen.ObjectAttr(key='id', value=index + 1)
                gen.ObjectAttr(key='name', value=name)
                for lang in UI_LANGUAGES:
                    gen.ObjectAttr(key=lang, value=replace_templates(self.find_keyword(keyword, lang=lang)[1]))

        print(f'Write {output_file}')
        gen.write(output_file)

    def load_daily_quests_keywords(self, lang='cn'):
        daily_quest = read_file(os.path.join(TextMap.DATA_FOLDER, 'ExcelOutput', 'DailyQuest.json'))
        quest_data = read_file(os.path.join(TextMap.DATA_FOLDER, 'ExcelOutput', 'QuestData.json'))
        quests_hash = [quest_data[quest_id]["QuestTitle"]["Hash"] for quest_id in daily_quest]
        quest_keywords = [self.text_map[lang].find(quest_hash)[1] for quest_hash in quests_hash]
        self.load_keywords(quest_keywords, lang)

    def generate(self):
        self.load_keywords(['模拟宇宙', '拟造花萼（金）', '拟造花萼（赤）', '凝滞虚影', '侵蚀隧洞', '历战余响', '忘却之庭'])
        self.write_keywords(keyword_class='DungeonNav', output_file='./tasks/dungeon/keywords/nav.py')
        self.load_keywords(['行动摘要', '生存索引', '每日实训'])
        self.write_keywords(keyword_class='DungeonTab', output_file='./tasks/dungeon/keywords/tab.py')
        self.load_daily_quests_keywords()
        self.write_keywords(keyword_class='DailyQuest', output_file='./tasks/daily/keywords/daily_quest.py')
        self.load_keywords(list(self.iter_guide()))
        self.write_keywords(keyword_class='DungeonList', output_file='./tasks/dungeon/keywords/dungeon.py',
                            text_convert=dungeon_name)


if __name__ == '__main__':
    TextMap.DATA_FOLDER = '../StarRailData'
    KeywordExtract().generate()
