import os
import re

import numpy as np

from dev_tools.slpp import slpp
from module.base.utils import location2node
from module.map.map_base import camera_2d

"""
This an auto-tool to extract map files used in Alas.
"""

DIC_SIREN_NAME_CHI_TO_ENG = {
    # Siren cyan
    'sairenquzhu_i': 'DD',
    'sairenqingxun_i': 'CL',
    'sairenzhongxun_i': 'CA',
    'sairenzhanlie_i': 'BB',
    'sairenhangmu_i': 'CV',

    # Scherzo of Iron and Blood
    'aruituosha': 'Arethusa',
    'xiefeierde': 'Sheffield',
    'duosaitejun': 'Dorsetshire',
    'shengwang': 'Renown',
    'weiershiqinwang': 'PrinceOfWales'
}


def load_lua(folder, file, prefix):
    with open(os.path.join(folder, file), 'r', encoding='utf-8') as f:
        text = f.read()
    print(f'Loading {file}')
    result = slpp.decode(text[prefix:])
    print(f'{len(result.keys())} items loaded')
    return result


class MapData:
    dic_grid_info = {
        0: '--',
        1: 'SP',
        2: 'MM',
        3: 'MA',
        4: 'Me',  # This grid 100% spawn enemy?
        6: 'ME',
        8: 'MB',
        12: 'MS',
        16: '__'
    }

    def __init__(self, data, expedition_data):
        self.data = data
        self.expedition_data = expedition_data
        self.chapter_name = data['chapter_name'].replace('–', '-')
        self.name = data['name']
        self.profiles = data['profiles']
        self.map_id = data['id']
        battle_count = max(data['boss_refresh'], max(data['enemy_refresh'].keys()))
        self.spawn_data = [{'battle': index} for index in range(battle_count + 1)]
        try:
            # spawn_data
            for index, count in data['enemy_refresh'].items():
                if count:
                    spawn = self.spawn_data[index]
                    spawn['enemy'] = spawn.get('enemy', 0) + count
            if ''.join([str(item) for item in data['elite_refresh'].values()]) != '100':  # Some data is incorrect
                for index, count in data['elite_refresh'].items():
                    if count:
                        spawn = self.spawn_data[index]
                        spawn['enemy'] = spawn.get('enemy', 0) + count
            for index, count in data['ai_refresh'].items():
                if count:
                    spawn = self.spawn_data[index]
                    spawn['siren'] = spawn.get('siren', 0) + count
            for index, count in data['box_refresh'].items():
                if count:
                    spawn = self.spawn_data[index]
                    spawn['mystery'] = spawn.get('mystery', 0) + count
            self.spawn_data[data['boss_refresh']]['boss'] = 1

            # map_data
            # {0: {0: 6, 1: 8, 2: False, 3: 0}, ...}
            self.map_data = {}
            grids = data['grids']
            offset_y = min([grid[0] for grid in grids.values()])
            offset_x = min([grid[1] for grid in grids.values()])
            for grid in grids.values():
                loca = (grid[1] - offset_x, grid[0] - offset_y)
                if not grid[2]:
                    info = '++'
                else:
                    info = self.dic_grid_info.get(grid[3], '??')
                if info == '??':
                    print(f'Unknown grid info. grid={location2node(loca)}, info={grid[3]}')
                self.map_data[loca] = info
            self.shape = tuple(np.max(list(self.map_data.keys()), axis=0))

            # config
            self.MAP_SIREN_TEMPLATE = []
            self.MOVABLE_ENEMY_TURN = set()
            for siren_id in data['ai_expedition_list'].values():
                if siren_id == 1:
                    continue
                exped_data = expedition_data[siren_id]
                name = exped_data['icon']
                name = DIC_SIREN_NAME_CHI_TO_ENG.get(name, name)
                self.MAP_SIREN_TEMPLATE.append(name)
                self.MOVABLE_ENEMY_TURN.add(int(exped_data['ai_mov']))
            self.MAP_HAS_MAP_STORY = len(data['story_refresh_boss']) > 0
            self.MAP_HAS_FLEET_STEP = bool(data['is_limit_move'])
        except Exception as e:
            for k, v in data.items():
                print(f'{k} = {v}')
            raise e

    def __str__(self):
        return f'{self.map_id} {self.chapter_name} {self.name}'

    __repr__ = __str__

    def map_file_name(self):
        name = self.chapter_name.replace('-', '_').lower()
        if name[0].isdigit():
            name = f'campaign_{name}'
        return name + '.py'

    def get_file_lines(self):
        """
        Returns:
            list(str): Python code in map file.
        """
        header = """
            from module.campaign.campaign_base import CampaignBase
            from module.map.map_base import CampaignMap
            from module.map.map_grids import SelectedGrids, RoadGrids
            from module.logger import logger
        """
        lines = []

        # Import
        for head in header.strip().split('\n'):
            lines.append(head.strip())
        if self.chapter_name[-1].isdigit():
            chap, stage = self.chapter_name[:-1], self.chapter_name[-1]
            if stage != '1':
                lines.append(f'from .{chap.lower()}1 import Config as ConfigBase')
        lines.append('')

        # Map
        lines.append(f'MAP = CampaignMap(\'{self.chapter_name}\')')
        lines.append(f'MAP.shape = \'{location2node(self.shape)}\'')
        lines.append(
            f'MAP.camera_data = {[location2node(loca) for loca in camera_2d(self.shape, sight=(-3, -1, 3, 2))]}')
        lines.append(f'MAP.camera_data_spawn_point = []')
        lines.append('MAP.map_data = \"\"\"')
        for y in range(self.shape[1] + 1):
            lines.append('    ' + ' '.join([self.map_data[(x, y)] for x in range(self.shape[0] + 1)]))
        lines.append('\"\"\"')
        lines.append('MAP.weight_data = \"\"\"')
        for y in range(self.shape[1] + 1):
            lines.append('    ' + ' '.join(['10'] * (self.shape[0] + 1)))
        lines.append('\"\"\"')
        lines.append('MAP.spawn_data = [')
        for battle in self.spawn_data:
            lines.append('    ' + str(battle) + ',')
        lines.append(']')
        for y in range(self.shape[1] + 1):
            lines.append(', '.join([location2node((x, y)) for x in range(self.shape[0] + 1)]) + ', \\')
        lines.append('    = MAP.flatten()')
        lines.append('')
        lines.append('')

        # Config
        if self.chapter_name[-1].isdigit():
            chap, stage = self.chapter_name[:-1], self.chapter_name[-1]
            if stage != '1':
                lines.append('class Config(ConfigBase):')
            else:
                lines.append('class Config:')
        else:
            lines.append('class Config:')
        # lines.append('    pass')
        if len(self.MAP_SIREN_TEMPLATE):
            lines.append(f'    MAP_SIREN_TEMPLATE = {self.MAP_SIREN_TEMPLATE}')
            lines.append(f'    MOVABLE_ENEMY_TURN = {tuple(self.MOVABLE_ENEMY_TURN)}')
            lines.append(f'    MAP_HAS_SIREN = True')
        lines.append(f'    MAP_HAS_MAP_STORY = {self.MAP_HAS_MAP_STORY}')
        lines.append(f'    MAP_HAS_FLEET_STEP = {self.MAP_HAS_FLEET_STEP}')
        lines.append('')
        lines.append('')

        # Campaign
        lines.append('class Campaign(CampaignBase):')
        lines.append('    MAP = MAP')
        lines.append('')
        lines.append('    def battle_0(self):')
        if len(self.MAP_SIREN_TEMPLATE):
            lines.append('        if self.clear_siren():')
            lines.append('            return True')
            lines.append('')
        lines.append('        return self.battle_default()')
        lines.append('')
        lines.append(f'    def battle_{self.data["boss_refresh"]}(self):')
        lines.append('        return self.fleet_boss.clear_boss()')

        return lines

    def write(self, path):
        file = os.path.join(path, self.map_file_name())
        if os.path.exists(file):
            print(f'File exists: {file}')
            return False
        print(f'Extract: {file}')
        with open(file, 'w') as f:
            for text in self.get_file_lines():
                f.write(text + '\n')


class ChapterTemplate:
    def __init__(self, file):
        self.data = load_lua(file, 'chapter_template.lua', prefix=36)
        self.expedition_data = load_lua(file, 'expedition_data_template.lua', prefix=43)

    def get_chapter_by_name(self, name, select=False):
        """
        11004 (map id) --> 10-4 Hard
        ↑-- ↑
        | | +-- stage index
        | +---- chapter index
        +------ 1 for hard, 0 for normal

        1140017 (map id) --> Iris of Light and Dark D2
        ---  ↑↑
         ↑   |+-- stage index
         |   +--- chapter index
         +------- event index, >=210 for war achieve

        Args:
            name (str, int): A keyword from chapter name, such as '短兵相接', '正义的怒吼'
                Or map_id such as 702, 1140017
            select (bool): False means only extract this map, True means all maps from this event

        Returns:
            list(MapData):
        """
        print('<<< SEARCH MAP >>>')
        name = name.strip()
        name = int(name) if name.isdigit() else name
        print(f'Searching: {name}')
        if isinstance(name, str):
            maps = []
            for map_id, data in self.data.items():
                if not isinstance(map_id, int) or data['chapter_name'] == 'EXTRA':
                    continue
                if not re.search(name, data['name']):
                    continue
                data = MapData(data, self.expedition_data)
                print(f'Found map: {data}')
                maps.append(data)
        else:
            data = MapData(self.data[name], self.expedition_data)
            print(f'Found map: {data}')
            maps = [data]

        if not len(maps):
            print('No maps found')
            return []
        print('')

        print('<<< SELECT MAP >>>')

        def get_event_id(map_id):
            return (map_id - 2100000) // 20 + 21000 if map_id // 10000 == 210 else map_id // 10000

        if select:
            event_id = get_event_id(maps[0].map_id)
            new = []
            for map_id, data in self.data.items():
                if not isinstance(map_id, int) or data['chapter_name'] == 'EXTRA':
                    continue
                if get_event_id(data['id']) == event_id:
                    data = MapData(data, self.expedition_data)
                    print(f'Selected: {data}')
                    new.append(data)
            maps = new
        else:
            maps = maps[:1]
            print(f'Selected: {maps[0]}')

        print('')
        return maps

    def extract(self, maps, folder):
        """
        Args:
            maps (list[MapData]):
            folder (str):
        """
        print('<<< CONFIRM >>>')
        print('Please confirm selected the correct maps before extracting. Will skip existing files.\n'
              'Input any key and press ENTER to continue')
        input()

        if not os.path.exists(folder):
            os.mkdir(folder)
        for data in maps:
            data.write(folder)


"""
This an auto-tool to extract map files used in Alas.

Git clone https://github.com/Dimbreath/AzurLaneData, to get the decrypted scripts.
Arguments:
    FILE:    Folder contains `chapter_template.lua` and `expedition_data_template.lua`, 
             Such as '<your_folder>/<server>/sharecfg'
    FOLDER:  Folder to save, './campaign/test'
    KEYWORD: A keyword in map name, such as '短兵相接' (7-2, zh-CN), 'Counterattack!' (3-4, en-US)
             Or map id, such as 702 (7-2), 1140017 (Iris of Light and Dark D2)
    SELECT:  True if select all maps in the same event
             False if extract this map only
"""
FILE = ''
FOLDER = './campaign/test'
KEYWORD = ''
SELECT = False

ct = ChapterTemplate(FILE)
ct.extract(ct.get_chapter_by_name(KEYWORD, select=SELECT), folder=FOLDER)
