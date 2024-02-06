import re
import typing as t

from dev_tools.keywords.base import GenerateKeyword, text_to_variable
from module.base.decorator import cached_property
from module.config.utils import deep_get


def dungeon_name(name: str) -> str:
    name = text_to_variable(name)
    name = re.sub('Bud_of_(Memories|Aether|Treasures)', r'Calyx_Golden_\1', name)
    name = re.sub('Bud_of_(.*)', r'Calyx_Crimson_\1', name).replace('Calyx_Crimson_Calyx_Crimson_', 'Calyx_Crimson_')
    name = re.sub('Shape_of_(.*)', r'Stagnant_Shadow_\1', name)
    name = re.sub('Path_of_(.*)', r'Cavern_of_Corrosion_Path_of_\1', name)
    if name in ['Destruction_Beginning', 'End_of_the_Eternal_Freeze', 'Divine_Seed', 'Borehole_Planet_Old_Crater']:
        name = f'Echo_of_War_{name}'
    if name in ['The_Swarm_Disaster', 'Gold_and_Gears']:
        name = f'Simulated_Universe_{name}'
    return name


class GenerateDungeonList(GenerateKeyword):
    output_file = './tasks/dungeon/keywords/dungeon.py'

    @cached_property
    def data(self):
        return self.read_file('./ExcelOutput/GameplayGuideData.json')

    def iter_keywords(self) -> t.Iterable[dict]:
        for keyword in self.iter_dungeon():
            if isinstance(keyword, str):
                yield dict(
                    text_id=self.find_keyword(keyword, lang='cn')[0],
                    plane_id=-1,
                )
            else:
                yield keyword

    def iter_dungeon(self):
        temp_save = ""
        for data in self.data.values():
            text_id = deep_get(data, keys='Name.Hash')
            plane_id = deep_get(data, 'MapEntranceID', 0)
            _, name = self.find_keyword(text_id, lang='cn')
            if '永屹之城遗秘' in name:  # load after all forgotten hall to make sure the same order in Game UI
                temp_save = text_id
                continue
            if '忘却之庭' in name:
                continue
            yield dict(
                text_id=text_id,
                plane_id=plane_id,
            )
        if temp_save:
            yield temp_save
        # Consider rogue DLC as a dungeon
        yield '寰宇蝗灾'
        yield '黄金与机械'
        # 'Memory of Chaos' is not a real dungeon, but represents a group
        yield '混沌回忆'
        yield '天艟求仙迷航录'
        yield '永屹之城遗秘'

    def convert_name(self, text: str, keyword: dict) -> str:
        text = super().convert_name(text, keyword=keyword)
        text = dungeon_name(text)

        # Add plane suffix
        from tasks.map.keywords import MapPlane

        if text.startswith('Calyx_Crimson'):
            plane = MapPlane.find_plane_id(keyword['plane_id'])
            text = f'{text}_{plane.name}'
        return text

    def iter_rows(self) -> t.Iterable[dict]:
        dungeons = list(super().iter_rows())
        calyx = []
        order = [
            'Calyx_Golden',
            'Calyx_Crimson_Destruction',
            'Calyx_Crimson_Preservation',
            'Calyx_Crimson_The_Hunt',
            'Calyx_Crimson_Abundance',
            'Calyx_Crimson_Erudition',
            'Calyx_Crimson_Harmony',
            'Calyx_Crimson_Nihility',
        ]
        for keyword in order:
            condition = lambda x: x['name'].startswith(keyword)
            print([d for d in dungeons])
            calyx += [d for d in dungeons if condition(d)]
            dungeons = [d for d in dungeons if not condition(d)]
        dungeons = calyx + dungeons

        for row in dungeons:
            yield row
