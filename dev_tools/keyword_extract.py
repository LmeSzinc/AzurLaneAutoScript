import os
import re
import typing as t
from collections import namedtuple
from functools import cached_property

from module.base.code_generator import CodeGenerator
from module.config.utils import deep_get, read_file
from module.logger import logger

UI_LANGUAGES = ['cn', 'cht', 'en', 'jp', 'es']


def text_to_variable(text):
    text = re.sub("'s |s' ", '_', text)
    text = re.sub('[ \-—:\'/•.]+', '_', text)
    text = re.sub(r'[(),#"?!&]|</?\w+>', '', text)
    # text = re.sub(r'[#_]?\d+(_times?)?', '', text)
    return text


def dungeon_name(name: str) -> str:
    name = text_to_variable(name)
    name = re.sub('Bud_of_(Memories|Aether|Treasures)', r'Calyx_Golden_\1', name)
    name = re.sub('Bud_of_(.*)', r'Calyx_Crimson_\1', name).replace('Calyx_Crimson_Calyx_Crimson_', 'Calyx_Crimson_')
    name = re.sub('Shape_of_(.*)', r'Stagnant_Shadow_\1', name)
    name = re.sub('Path_of_(.*)', r'Cavern_of_Corrosion_Path_of_\1', name)
    if name in ['Destruction_Beginning', 'End_of_the_Eternal_Freeze', 'Divine_Seed']:
        name = f'Echo_of_War_{name}'
    return name


def blessing_name(name: str) -> str:
    name = text_to_variable(name)
    name = re.sub(r'^\d', lambda match: f"_{match.group(0)}", name)
    return name


nickname_count = 0


def character_name(name: str) -> str:
    name = text_to_variable(name)
    name = re.sub('_', '', name)
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
        self.text_map['cn'] = TextMap('chs')
        self.keywords_id: list[int] = []

    def iter_guide(self) -> t.Iterable[int]:
        file = os.path.join(TextMap.DATA_FOLDER, './ExcelOutput/GameplayGuideData.json')
        # visited = set()
        temp_save = ""
        for data in read_file(file).values():
            hash_ = deep_get(data, keys='Name.Hash')
            _, name = self.find_keyword(hash_, lang='cn')
            if '永屹之城遗秘' in name:  # load after all forgotten hall to make sure the same order in Game UI
                temp_save = hash_
                continue
            if '忘却之庭' in name:
                continue
                # if name in visited:
                #     continue
                # visited.add(name)
            yield hash_
        yield temp_save
        # 'Memory of Chaos' is not a real dungeon, but represents a group
        yield '混沌回忆'

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
            generator: CodeGenerator = None,
            extra_attrs: dict[str, dict] = None
    ):
        """
        Args:
            keyword_class:
            output_file:
            text_convert:
            generator: Reuse an existing code generator
            extra_attrs: Extra attributes write in keywords
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
        if extra_attrs:
            keyword_num = len(self.keywords_id)
            for attr_key, attr_value in extra_attrs.items():
                if len(attr_value) != keyword_num:
                    print(f"Extra attribute {attr_key} does not match the size of keywords")
                    return
        for index, keyword in enumerate(self.keywords_id):
            _, name = self.find_keyword(keyword, lang='en')
            name = text_convert(replace_templates(name))
            with gen.Object(key=name, object_class=keyword_class):
                gen.ObjectAttr(key='id', value=index + last_id + 1)
                gen.ObjectAttr(key='name', value=name)
                for lang in UI_LANGUAGES:
                    gen.ObjectAttr(key=lang, value=replace_templates(self.find_keyword(keyword, lang=lang)[1]))
                if extra_attrs:
                    for attr_key, attr_value in extra_attrs.items():
                        gen.ObjectAttr(key=attr_key, value=attr_value[keyword])
                gen.last_id = index + last_id + 1

        if output_file:
            print(f'Write {output_file}')
            gen.write(output_file)
            self.clear_keywords()
        return gen

    def load_quests(self, quests, lang='cn'):
        """
        Load a set of quest keywords

        Args:
            quests: iterable quest id collection
            lang:

        """
        quest_data = read_file(os.path.join(TextMap.DATA_FOLDER, 'ExcelOutput', 'QuestData.json'))
        quests_hash = [quest_data[str(quest_id)]["QuestTitle"]["Hash"] for quest_id in quests]
        quest_keywords = list(dict.fromkeys([self.text_map[lang].find(quest_hash)[1] for quest_hash in quests_hash]))
        self.load_keywords(quest_keywords, lang)

    def generate_daily_quests(self):
        daily_quest = read_file(os.path.join(TextMap.DATA_FOLDER, 'ExcelOutput', 'DailyQuest.json'))
        self.load_quests(daily_quest.keys())
        self.write_keywords(keyword_class='DailyQuest', output_file='./tasks/daily/keywords/daily_quest.py')

    def load_character_name_keywords(self, lang='en'):
        file_name = 'ItemConfigAvatarPlayerIcon.json'
        path = os.path.join(TextMap.DATA_FOLDER, 'ExcelOutput', file_name)
        character_data = read_file(path)
        characters_hash = [character_data[key]["ItemName"]["Hash"] for key in character_data]

        text_map = self.text_map[lang]
        keywords_id = sorted(
            {text_map.find(keyword)[1] for keyword in characters_hash}
        )
        self.load_keywords(keywords_id, lang)

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
            'Special': ['黑塔的办公室', '锋芒崭露'],
            'Rogue': [ '区域-战斗', '区域-事件', '区域-遭遇', '区域-休整', '区域-精英', '区域-首领', '区域-交易'],
            'Herta': ['观景车厢', '主控舱段', '基座舱段', '收容舱段', '支援舱段'],
            'Jarilo': ['行政区', '城郊雪原', '边缘通路', '铁卫禁区', '残响回廊', '永冬岭',
                       '磐岩镇', '大矿区', '铆钉镇', '机械聚落'],
            'Luofu': ['星槎海中枢', '流云渡', '迴星港', '长乐天', '金人巷', '太卜司', '工造司', '丹鼎司', '鳞渊境'],
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

    def generate_character_keywords(self):
        self.load_character_name_keywords()
        self.write_keywords(keyword_class='CharacterList', output_file='./tasks/character/keywords/character_list.py',
                            text_convert=character_name)

    def generate_battle_pass_quests(self):
        battle_pass_quests = read_file(os.path.join(TextMap.DATA_FOLDER, 'ExcelOutput', 'BattlePassConfig.json'))
        latest_quests = list(battle_pass_quests.values())[-1]
        quests = deep_get(latest_quests, "DailyQuestList") + deep_get(latest_quests, "WeekQuestList") + deep_get(
            latest_quests, "WeekOrder1")
        self.load_quests(quests)
        self.write_keywords(keyword_class='BattlePassQuest', output_file='./tasks/battle_pass/keywords/quest.py')

    def generate_rogue_buff(self):
        # paths
        aeons = read_file(os.path.join(TextMap.DATA_FOLDER, 'ExcelOutput', 'RogueAeonDisplay.json'))
        aeons_hash = [deep_get(aeon, 'RogueAeonPathName2.Hash') for aeon in aeons.values()]
        self.keywords_id = aeons_hash
        self.write_keywords(keyword_class='RoguePath', output_file='./tasks/rogue/keywords/path.py')

        # blessings
        blessings_info = read_file(os.path.join(TextMap.DATA_FOLDER, 'ExcelOutput', 'RogueBuff.json'))
        blessings_name_map = read_file(os.path.join(TextMap.DATA_FOLDER, 'ExcelOutput', 'RogueMazeBuff.json'))
        blessings_id = [deep_get(blessing, '1.MazeBuffID') for blessing in blessings_info.values()
                        if not deep_get(blessing, '1.AeonID')][1:]
        resonances_id = [deep_get(blessing, '1.MazeBuffID') for blessing in blessings_info.values()
                         if deep_get(blessing, '1.AeonID')]

        def get_blessing_infos(id_list, with_enhancement: bool):
            blessings_hash = [deep_get(blessings_name_map, f"{blessing_id}.1.BuffName.Hash")
                              for blessing_id in id_list]
            blessings_path_id = {blessing_hash: int(deep_get(blessings_info, f'{blessing_id}.1.RogueBuffType')) - 119
                                 # 119 is the magic number make type match with path in keyword above
                                 for blessing_hash, blessing_id in zip(blessings_hash, id_list)}
            blessings_rarity = {blessing_hash: deep_get(blessings_info, f'{blessing_id}.1.RogueBuffRarity')
                                for blessing_hash, blessing_id in zip(blessings_hash, id_list)}
            enhancement = {blessing_hash: "" for blessing_hash in blessings_hash}
            if with_enhancement:
                return blessings_hash, {'path_id': blessings_path_id, 'rarity': blessings_rarity,
                                        'enhancement': enhancement}
            else:
                return blessings_hash, {'path_id': blessings_path_id, 'rarity': blessings_rarity}

        hash_list, extra_attrs = get_blessing_infos(blessings_id, with_enhancement=True)
        self.keywords_id = hash_list
        self.write_keywords(keyword_class='RogueBlessing', output_file='./tasks/rogue/keywords/blessing.py',
                            text_convert=blessing_name, extra_attrs=extra_attrs)

        hash_list, extra_attrs = get_blessing_infos(resonances_id, with_enhancement=False)
        self.keywords_id = hash_list
        self.write_keywords(keyword_class='RogueResonance', output_file='./tasks/rogue/keywords/resonance.py',
                            text_convert=blessing_name, extra_attrs=extra_attrs)

    def iter_without_duplication(self, file: dict, keys):
        visited = set()
        for data in file.values():
            hash_ = deep_get(data, keys=keys)
            _, name = self.find_keyword(hash_, lang='cn')
            if name in visited:
                continue
            visited.add(name)
            yield hash_

    def generate(self):
        self.load_keywords(['模拟宇宙', '拟造花萼（金）', '拟造花萼（赤）', '凝滞虚影', '侵蚀隧洞', '历战余响', '忘却之庭'])
        self.write_keywords(keyword_class='DungeonNav', output_file='./tasks/dungeon/keywords/nav.py')
        self.load_keywords(['行动摘要', '生存索引', '每日实训'])
        self.write_keywords(keyword_class='DungeonTab', output_file='./tasks/dungeon/keywords/tab.py')
        self.load_keywords(['前往', '领取', '进行中', '已领取', '本日活跃度已满'])
        self.write_keywords(keyword_class='DailyQuestState', output_file='./tasks/daily/keywords/daily_quest_state.py')
        self.load_keywords(['领取', '追踪'])
        self.write_keywords(keyword_class='BattlePassQuestState',
                            output_file='./tasks/battle_pass/keywords/quest_state.py')
        self.load_keywords(list(self.iter_guide()))
        self.write_keywords(keyword_class='DungeonList', output_file='./tasks/dungeon/keywords/dungeon.py',
                            text_convert=dungeon_name)
        self.load_keywords(['传送', '追踪'])
        self.write_keywords(keyword_class='DungeonEntrance', output_file='./tasks/dungeon/keywords/dungeon_entrance.py')
        self.load_keywords(['奖励', '任务', ])
        self.write_keywords(keyword_class='BattlePassTab', output_file='./tasks/battle_pass/keywords/tab.py')
        self.load_keywords(['本日任务', '本周任务', '本期任务'])
        self.write_keywords(keyword_class='BattlePassMissionTab',
                            output_file='./tasks/battle_pass/keywords/mission_tab.py')
        self.generate_assignment_keywords()
        self.generate_forgotten_hall_stages()
        self.generate_map_planes()
        self.generate_character_keywords()
        self.generate_daily_quests()
        self.generate_battle_pass_quests()
        self.load_keywords(['养成材料', '光锥', '遗器', '其他材料', '消耗品', '任务', '贵重物'])
        self.write_keywords(keyword_class='ItemTab', text_convert=lambda name: name.replace(' ', ''),
                            output_file='./tasks/item/keywords/tab.py')
        self.generate_rogue_buff()
        self.load_keywords(['已强化'])
        self.write_keywords(keyword_class='RogueEnhancement', output_file='./tasks/rogue/keywords/enhancement.py')
        self.load_keywords(list(self.iter_without_duplication(
            read_file(os.path.join(TextMap.DATA_FOLDER, 'ExcelOutput', 'RogueMiracleDisplay.json')),
            'MiracleName.Hash')))
        self.write_keywords(keyword_class='RogueCurio', output_file='./tasks/rogue/keywords/curio.py')
        self.load_keywords(list(self.iter_without_duplication(
            read_file(os.path.join(TextMap.DATA_FOLDER, 'ExcelOutput', 'RogueBonus.json')), 'BonusTitle.Hash')))
        self.write_keywords(keyword_class='RogueBonus', output_file='./tasks/rogue/keywords/bonus.py')


if __name__ == '__main__':
    TextMap.DATA_FOLDER = '../StarRailData'
    KeywordExtract().generate()
