import os
import re
import typing as t
from collections import namedtuple
from functools import cached_property

from module.base.code_generator import CodeGenerator
from module.config.utils import deep_get, read_file
from module.logger import logger

UI_LANGUAGES = ['cn', 'cht', 'en', 'jp']


def text_to_variable(text):
    text = re.sub("'s |s' ", '_', text)
    text = re.sub('[ \-—:\'/]+', '_', text)
    text = re.sub(r'[(),#]|</?\w+>', '', text)
    # text = re.sub(r'[#_]?\d+(_times?)?', '', text)
    return text


def dungeon_name(name: str) -> str:
    name = text_to_variable(name)
    name = re.sub('Bud_of_(Memories|Aether|Treasures)', r'Calyx_Golden_\1', name)
    name = re.sub('Bud_of_(.*)', r'Calyx_Crimson_\1', name).replace('Calyx_Crimson_Calyx_Crimson_', 'Calyx_Crimson_')
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
        visited = set()
        for data in read_file(file).values():
            hash_ = deep_get(data, keys='Name.Hash')
            _, name = self.find_keyword(hash_, lang='cn')
            if '忘却之庭' in name:
                if name in visited:
                    continue
                visited.add(name)
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
        keywords_id = [text_map.find(keyword)[0] for keyword in keywords]
        self.keywords_id = [keyword for keyword in keywords_id if keyword != 0]

    def clear_keywords(self):
        self.keywords_id = []

    def write_keywords(
            self,
            keyword_class,
            output_file: str = '',
            text_convert=text_to_variable,
            generator: CodeGenerator = None
    ):
        """
        Args:
            keyword_class:
            output_file:
            text_convert:
            generator: Reuse an existing code generator
        """
        if generator is None:
            gen = CodeGenerator()
            gen.Import(f"""
            from .classes import {keyword_class}
            """)
            gen.CommentAutoGenerage('dev_tools.keyword_extract')
        else:
            gen = generator

        last_id = getattr(gen, 'last_id', 0)
        for index, keyword in enumerate(self.keywords_id):
            _, name = self.find_keyword(keyword, lang='en')
            name = text_convert(replace_templates(name))
            with gen.Object(key=name, object_class=keyword_class):
                gen.ObjectAttr(key='id', value=index + last_id + 1)
                gen.ObjectAttr(key='name', value=name)
                for lang in UI_LANGUAGES:
                    gen.ObjectAttr(key=lang, value=replace_templates(self.find_keyword(keyword, lang=lang)[1]))
                gen.last_id = index + last_id + 1

        if output_file:
            print(f'Write {output_file}')
            gen.write(output_file)
            self.clear_keywords()
        return gen

    def load_daily_quests_keywords(self, lang='cn'):
        daily_quest = read_file(os.path.join(TextMap.DATA_FOLDER, 'ExcelOutput', 'DailyQuest.json'))
        quest_data = read_file(os.path.join(TextMap.DATA_FOLDER, 'ExcelOutput', 'QuestData.json'))
        quests_hash = [quest_data[quest_id]["QuestTitle"]["Hash"] for quest_id in daily_quest]
        quest_keywords = [self.text_map[lang].find(quest_hash)[1] for quest_hash in quests_hash]
        self.load_keywords(quest_keywords, lang)

    def generate_forgotten_hall_stages(self):
        keyword_class = "ForgottenHallStage"
        output_file = './tasks/forgotten_hall/keywords/stage.py'
        gen = CodeGenerator()
        gen.Import(f"""
        from .classes import {keyword_class}
        """)
        gen.CommentAutoGenerage('dev_tools.keyword_extract')
        for stage_id in range(1, 16):
            id_str = str(stage_id).rjust(2, '0')
            with gen.Object(key=f"Stage_{stage_id}", object_class=keyword_class):
                gen.ObjectAttr(key='id', value=stage_id)
                gen.ObjectAttr(key='name', value=id_str)
                for lang in UI_LANGUAGES:
                    gen.ObjectAttr(key=lang, value=id_str)

        print(f'Write {output_file}')
        gen.write(output_file)
        self.clear_keywords()

    def generate_assignment_keywords(self):
        KeywordFromFile = namedtuple('KeywordFromFile', ('file', 'class_name', 'output_file'))
        for keyword in (
                KeywordFromFile('ExpeditionGroup.json', 'AssignmentGroup', './tasks/assignment/keywords/group.py'),
                KeywordFromFile('ExpeditionData.json', 'AssignmentEntry', './tasks/assignment/keywords/entry.py')
        ):
            file = os.path.join(TextMap.DATA_FOLDER, 'ExcelOutput', keyword.file)
            self.load_keywords(deep_get(data, 'Name.Hash') for data in read_file(file).values())
            self.write_keywords(keyword_class=keyword.class_name, output_file=keyword.output_file)

    def generate_map_planes(self):
        planes = {
            'Herta': ['观景车厢', '主控舱段', '基座舱段', '收容舱段', '支援舱段'],
            'Jarilo': ['行政区', '城郊雪原', '边缘通路', '铁卫禁区', '残响回廊', '永冬岭',
                       '磐岩镇', '大矿区', '铆钉镇', '机械聚落'],
            'Luofu': ['星槎海中枢', '长乐天', '流云渡', '迴星港', '太卜司', '工造司'],
        }

        def text_convert(world_):
            def text_convert_wrapper(name):
                name = text_to_variable(name).replace('_', '')
                name = f'{world_}_{name}'
                return name

            return text_convert_wrapper

        gen = None
        for world, plane in planes.items():
            self.load_keywords(plane)
            gen = self.write_keywords(keyword_class='MapPlane', output_file='',
                                      text_convert=text_convert(world), generator=gen)
        gen.write('./tasks/map/keywords/plane.py')

    def generate(self):
        self.load_keywords(['模拟宇宙', '拟造花萼（金）', '拟造花萼（赤）', '凝滞虚影', '侵蚀隧洞', '历战余响', '忘却之庭'])
        self.write_keywords(keyword_class='DungeonNav', output_file='./tasks/dungeon/keywords/nav.py')
        self.load_keywords(['行动摘要', '生存索引', '每日实训'])
        self.write_keywords(keyword_class='DungeonTab', output_file='./tasks/dungeon/keywords/tab.py')
        self.load_daily_quests_keywords()
        self.write_keywords(keyword_class='DailyQuest', output_file='./tasks/daily/keywords/daily_quest.py')
        self.load_keywords(['前往', '领取', '进行中', '已领取', '本日活跃度已满'])
        self.write_keywords(keyword_class='DailyQuestState', output_file='./tasks/daily/keywords/daily_quest_state.py')
        self.load_keywords(list(self.iter_guide()))
        self.write_keywords(keyword_class='DungeonList', output_file='./tasks/dungeon/keywords/dungeon.py',
                            text_convert=dungeon_name)
        self.load_keywords(['传送', '追踪'])
        self.write_keywords(keyword_class='DungeonEntrance', output_file='./tasks/dungeon/keywords/dungeon_entrance.py')
        self.load_keywords(['奖励', '任务'])
        self.write_keywords(keyword_class='BattlePassTab', output_file='./tasks/battle_pass/keywords/tab.py')
        self.generate_assignment_keywords()
        self.generate_forgotten_hall_stages()
        self.generate_map_planes()
        self.load_keywords(['养成材料', '光锥', '遗器', '其他材料', '消耗品', '任务', '贵重物'])
        self.write_keywords(keyword_class='ItemTab', text_convert=lambda name: name.replace(' ', ''),
                            output_file='./tasks/item/keywords/tab.py')


if __name__ == '__main__':
    TextMap.DATA_FOLDER = '../StarRailData'
    KeywordExtract().generate()
