import os
import re

from dev_tools.slpp import slpp
from dev_tools.utils import LuaLoader
from module.base.utils import location2node
from module.logger import logger
from module.map.utils import *

"""
This an auto-tool to extract map files used in Alas.
"""

DIC_SIREN_NAME_CHI_TO_ENG = {
    # Siren Winter's Crown, Fallen Wings
    'sairenquzhu': 'DD',
    'sairenqingxun': 'CL',
    'sairenzhongxun': 'CA',
    'sairenzhanlie': 'BB',
    'sairenhangmu': 'CV',
    'sairenqianting': 'SS',

    # Siren cyan
    'sairenquzhu_i': 'DD',
    'sairenqingxun_i': 'CL',
    'sairenzhongxun_i': 'CA',
    'sairenzhanlie_i': 'BB',
    'sairenhangmu_i': 'CV',
    'sairenqianting_i': 'SS',

    # Siren red
    'sairenquzhu_M': 'DD',
    'sairenqingxun_M': 'CL',
    'sairenzhongxun_M': 'CAred',
    'sairenzhanlie_M': 'BBred',
    'sairenhangmu_M': 'CV',
    'sairenqianting_M': 'SS',

    # Scherzo of Iron and Blood
    'aruituosha': 'Arethusa',
    'xiefeierde': 'Sheffield',
    'duosaitejun': 'Dorsetshire',
    'shengwang': 'Renown',
    'weiershiqinwang': 'PrinceOfWales',

    # Universe in Unison
    'edu_idol': 'LeMalinIdol',
    'daiduo_idol': 'DidoIdol',
    'daqinghuayu_idol': 'AlbacoreIdol',
    'baerdimo_idol': 'BaltimoreIdol',
    'kelifulan_idol': 'ClevelandIdol',
    'xipeier_idol': 'HipperIdol',
    'sipeibojue_5': 'SpeeIdol',
    'luoen_idol': 'RoonIdol',
    'guanghui_idol': 'IllustriousIdol',

    # Vacation Lane
    'maliluosi_doa': 'MarieRoseDOA',
    'haixiao_doa': 'MisakiDOA',
    'xia_doa': 'KasumiDOA',
    'zhixiao_doa': 'NagisaDOA',

    # The Enigma and the Shark
    'nvjiang': 'Amazon',

    # Inverted Orthant
    'luodeni': 'Rodney',
    'huangjiafangzhou': 'ArkRoyal',
    'jingang': 'Kongo',
    'shancheng': 'Yamashiro',
    'z24': 'Z24',
    'niulunbao': 'Nuremberg',
    'longqibing': 'Carabiniere',
    # siren_ii has purple lightning around
    # Detect area of DD and CL are not effected
    'sairenquzhu_ii': 'DD',
    'sairenqingxun_ii': 'CL',
    'sairenzhongxun_ii': 'CAlightning',
    'sairenzhanlie_ii': 'BBlightning',
    'sairenhangmu_ii': 'CVlightning',
    'qinraozhe': 'Intruder',
    'xianghe': 'Shokaku',
    'ruihe': 'Zuikaku',
    'shitelasai': 'PeterStrasser',

    # Empyreal Tragicomedy
    'teluntuo': 'Trento',
    'lituoliao': 'Littorio',
    'jianyu': 'Swordfish',  # Not siren but movable enemy

    # Ashen Simulacrum
    'shengdiyage': 'SanDiego',
    'weiqita': 'Wichita',
    'yalisangna': 'Arizona',
    'liekexingdun': 'Lexington',
    'tiaoyu': 'Dace',

    # Daedalian Hymn
    'geluosite': 'Gloucester',
    'yueke': 'York',
    'yanzhan': 'Warspite',
    'naerxun': 'Nelson',
    'kewei': 'Formidable',
    'guanghui': 'Illustrious',

    # Mirror Involution
    # Note: In this event, sirens are covered by fog
    'duwei': 'Dewey',
    'haman': 'Hammann',
    'yatelanda': 'Atlanta',
    'beianpudun': 'Northampton',

    # Swirling Cherry Blossoms
    'xia': 'Kasumi',
    'xiang': 'Hibiki',
    'guinu': 'Kinu',
    'moye': 'Maya',
    'yishi': 'Ise',
    'sunying': 'Junyo',

    # Skybound Oratorio
    'aerjiliya': 'Algerie',
    'jialisuoniye': 'LaGalissonniere',
    'wokelan': 'Vauquelin',

    # Crimson Echoes
    'xili': 'Yuudachi',
    'shentong': 'Jintsuu',
    'niaohai': 'Choukai',
    'wudao': 'Kirishima',
    'canglong': 'Souryuu',

    # Tower of Transcendence
    'sairenquzhu_6': 'DD',
    'sairenqingxun_6': 'CL',
    'sairenzhongxun_6': 'CA',
    'sairenzhanlie_6': 'BB',
    'sairenhangmu_6': 'CV',

    # Northern Overture Rerun
    'ganraozhe': 'Intruder',

    # Abyssal Refrain
    'lingmin': 'Soobrazitelny',
    'jifu': 'Kiev',
    'fuerjia': 'Volga',

    # Aurora Noctis
    'U81': 'U81',
    'U101': 'U101',
    'U522': 'U522',
    'deyizhi': 'Deutschland',
    'tierbici': 'Tirpitz',
    'genaisennao': 'Gneisenau',
    'shaenhuosite': 'Scharnhorst',
    'sipeibojue': 'Spee',
    'U73': 'U73',

    # Rondo at Rainbow's End
    'z2': 'Z2',
    'laibixi': 'Leipzig',
    'ougen': 'PrinzEugen',
    'sairenqianting_ii': 'SS',
    'sairenboss11': 'Compiler',

    # Pledge of the Radiant Court
    'sizhannvshen': 'Bellona',
    'fuchou': 'Revenge',

    # Aquilifer's Ballade
    'tianhou_ghost': 'Juno_ghost',
    'haiwangxing_ghost': 'Neptune_ghost',
    'lemaer_ghost': 'LeMars_ghost',
    'jingjishen_ghost': 'Hermes_ghost',
    'qiubite_ghost': 'Jupiter_ghost',

    # Aquilifer's Ballade
    'z46': 'Z46',
    'haiyinlixi': 'PrinzHeinrich',
    'qibolin': 'GrafZeppelin',
    'magedebao': 'Magdeburg',
    'adaerbote': 'PrinzAdalbert',
    'weixi': 'Weser',
    'wuerlixi': 'UlrichVonHutten',

    # Violet Tempest Blooming Lycoris
    'ruoyue': 'Wakaba',
    'liangyue': 'Suzutsuki',
    'shenxue': 'Miyuki',
    'qifeng': 'Hatakaze',
    'yuhei': 'Haguro',
    'birui': 'Hiei',
    'zhenming': 'Haruna',
    'chicheng': 'Akagi',
    'jiahe': 'Kaga',
    'sanli': 'Mikasa',
    'changmen': 'Nagato',
    'jiuyun': 'Sakawa',
    'qiansui': 'Chitose',
    'qiandaitian': 'Chiyoda',
    'longfeng': 'Ryuuhou',
    'chunyue': 'Harutsuki',
    'jiangfeng': 'Kawakaze',

    # The Alchemist and the Archipelago of Secrets
    'lianjin_sairenquzhu': 'DDalchemist',
    'lianjin_sairenqingxun': 'CLalchemist',
    'lianjin_sairenzhongxun': 'CAalchemist',
    'lianjin_sairenzhanlie': 'BBalchemist',
    'lianjin_sairenhangmu': 'CValchemist',

    # Parallel Superimposition
    'sairenboss15': 'SirenBoss15',
    'sairenboss16': 'SirenBoss16',

    # Revelations of Dust
    'xiafei': 'Joffre',
    'lemaer': 'LeMars',

    # Confluence of Nothingness
    'shenyuanboss4': 'AbyssalBoss4',
    'shenyuanboss4_alter': 'AbyssalBoss4',
    'shenyuanboss5': 'AbyssalBoss5',
    'shenyuanboss5_alter': 'AbyssalBoss5',
    'sairenquzhu_m': 'DD',
    'sairenqingxun_m': 'CL',
    'sairenzhongxun_m': 'CAred',
    'sairenzhanlie_m': 'BBred',
    'sairenhangmu_m': 'CV',
    'sairenqianting_m': 'SS',

    # The Fool's Scales
    'sairenboss18': 'SirenBoss18',
    'sairenboss19': 'SirenBoss19',
    'srjiaohuangjijia': 'Dilloy',

    # Effulgence Before Eclipse
    'chuyue': 'Hatsuzuki',
    'zhaozhi': 'Asanagi',
    'ruifeng': 'Zuiho',

    'shanluan_sairenquzhu': 'SK_DD',
    'shanluan_sairenqingxun': 'SK_CL',
    'shanluan_sairenzhongxun': 'SK_CA',
    'shanluan_sairenzhanlie': 'SK_BB',
    'shanluan_sairenhangmu': 'SK_CV',

    # Light-Chasing Sea of Stars
    'sairenboss10': 'Sirenboss10',
    'UDFsairen_baolei_2': 'UDFFortress2',

    # Heart-Linking Harmony
    'lafei_6': 'Laffey6',
    'tashigan_idol': 'TashkentIdol',
    'xiefeierde_idol': 'SheffieldIdol',
    'yilishabai_3': 'Elizabeth3',
    'jiasikenie_idol': 'GascogneIdol',
    'dafeng_idol': 'TaihouIdol',

    # Interlude of Illusions
    'tianlangxing': 'Sirius',
    'daiduo': 'Dido',
    'z23_g': 'Z23_g',
    'laibixi_g': 'Leipzig_g',
    'pangpeimagenuo': 'PompeoMagno',
    'aerfuleiduo': 'AlfredoOriani',
    'guogan': 'LAudacieux',
    'dipulaikesi': 'Dupleix',
}


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
        16: '__',
        100: '++',  # Dock in Empyreal Tragicomedy
    }

    def __init__(self, data, data_loop):
        self.data = data
        self.data_loop = data_loop
        self.chapter_name = data['chapter_name'].replace('–', '-')
        self.name = data['name']
        self.profiles = data['profiles']
        self.map_id = data['id']

        try:
            self.spawn_data = self.parse_spawn_data(data)
            if data_loop is not None:
                self.spawn_data_loop = self.parse_spawn_data(data_loop)
                if len(self.spawn_data) == len(self.spawn_data_loop) \
                        and all([s1 == s2 for s1, s2 in zip(self.spawn_data, self.spawn_data_loop)]):
                    self.spawn_data_loop = None
            else:
                self.spawn_data_loop = None

            # map_data
            # {0: {0: 6, 1: 8, 2: False, 3: 0}, ...}
            self.map_data = self.parse_map_data(data['grids'])
            self.shape = tuple(np.max(list(self.map_data.keys()), axis=0))
            if self.data_loop is not None:
                self.map_data_loop = self.parse_map_data(data_loop['grids'])
                if all([d1 == d2 for d1, d2 in zip(self.map_data.values(), self.map_data_loop.values())]):
                    self.map_data_loop = None
            else:
                self.map_data_loop = None

            # portal
            self.portal = []
            # if self.map_id in MAP_EVENT_LIST:
            #     for event_id in MAP_EVENT_LIST[self.map_id]['event_list'].values():
            #         event = MAP_EVENT_TEMPLATE[event_id]
            #         for effect in event['effect'].values():
            #             if effect[0] == 'jump':
            #                 address = event['address']
            #                 address = location2node((address[1], address[0]))
            #                 target = location2node((effect[2], effect[1]))
            #                 self.portal.append((address, target))

            # land_based
            # land_based = {{6, 7, 1}, ...}
            # Format: {y, x, rotation}
            land_based_rotation_dict = {1: 'up', 2: 'down', 3: 'left', 4: 'right'}
            self.land_based = []
            if isinstance(data['land_based'], dict):
                for lb in data['land_based'].values():
                    y, x, r = lb.values()
                    if r not in land_based_rotation_dict:
                        continue
                    self.land_based.append([location2node((x, y)), land_based_rotation_dict[r]])

            # config
            self.MAP_SIREN_TEMPLATE = []
            self.MOVABLE_ENEMY_TURN = set()
            # Aquilifers Ballade (event_20220728_cn) has different sirens in clear mode
            sirens = list(data['ai_expedition_list'].values())
            if data_loop is not None and data_loop['ai_expedition_list'] is not None:
                sirens += list(data_loop['ai_expedition_list'].values())
            for siren_id in sirens:
                if siren_id == 1:
                    continue
                exped_data = EXPECTATION_DATA.get(siren_id, {})
                name = exped_data.get('icon', str(siren_id))
                name = DIC_SIREN_NAME_CHI_TO_ENG.get(name, name)
                if name not in self.MAP_SIREN_TEMPLATE:
                    self.MAP_SIREN_TEMPLATE.append(name)
                self.MOVABLE_ENEMY_TURN.add(int(exped_data.get('ai_mov', 2)))
            self.MAP_HAS_MOVABLE_ENEMY = bool(len(self.MOVABLE_ENEMY_TURN))
            self.MAP_HAS_MAP_STORY = len(data['story_refresh_boss']) > 0
            self.MAP_HAS_FLEET_STEP = bool(data['is_limit_move'])
            self.MAP_HAS_AMBUSH = bool(data['is_ambush']) or bool(data['is_air_attack'])
            self.MAP_HAS_MYSTERY = sum([b.get('mystery', 0) for b in self.spawn_data]) > 0
            self.MAP_HAS_PORTAL = bool(len(self.portal))
            self.MAP_HAS_LAND_BASED = bool(len(self.land_based))
            for n in range(1, 4):
                self.__setattr__(f'STAR_REQUIRE_{n}', data[f'star_require_{n}'])
        except Exception as e:
            for k, v in data.items():
                print(f'{k} = {v}')
            raise e

    def __str__(self):
        return f'{self.map_id} {self.chapter_name} {self.name}'

    __repr__ = __str__

    def parse_map_data(self, grids):
        map_data = {}
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
            map_data[loca] = info

        return map_data

    @staticmethod
    def parse_spawn_data(data):
        try:
            battle_count = max(data['boss_refresh'], max(data['enemy_refresh'].keys()))
        except ValueError:
            battle_count = 0
        spawn_data = [{'battle': index} for index in range(battle_count + 1)]

        for index, count in data['enemy_refresh'].items():
            if count:
                spawn = spawn_data[index]
                spawn['enemy'] = spawn.get('enemy', 0) + count
        if ''.join([str(item) for item in data['elite_refresh'].values()]) != '100':  # Some data is incorrect
            for index, count in data['elite_refresh'].items():
                if count:
                    spawn = spawn_data[index]
                    spawn['enemy'] = spawn.get('enemy', 0) + count
        for index, count in data['ai_refresh'].items():
            if count:
                spawn = spawn_data[index]
                spawn['siren'] = spawn.get('siren', 0) + count
        for index, count in data['box_refresh'].items():
            if count:
                spawn = spawn_data[index]
                spawn['mystery'] = spawn.get('mystery', 0) + count
        try:
            spawn_data[data['boss_refresh']]['boss'] = 1
        except IndexError:
            pass

        return spawn_data

    def map_file_name(self):
        name = self.chapter_name.replace('-', '_').lower()
        if name[0].isdigit():
            name = f'campaign_{name}'
        return name + '.py'

    def get_file_lines(self, has_modified_campaign_base):
        """
        Args:
            has_modified_campaign_base (bool): If target folder has modified campaign_base.py

        Returns:
            list(str): Python code in map file.
        """
        if IS_WAR_ARCHIVES:
            base_import = 'from ..campaign_war_archives.campaign_base import CampaignBase'
        elif has_modified_campaign_base:
            base_import = 'from .campaign_base import CampaignBase'
        else:
            base_import = 'from module.campaign.campaign_base import CampaignBase'

        header = f"""
            {base_import}
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
        camera_data = camera_2d(get_map_active_area(self.map_data), sight=(-3, -1, 3, 2))
        lines.append(
            f'MAP.camera_data = {[location2node(loca) for loca in camera_data]}')
        camera_sp = camera_spawn_point(camera_data, sp_list=[k for k, v in self.map_data.items() if v == 'SP'])
        lines.append(f'MAP.camera_data_spawn_point = {[location2node(loca) for loca in camera_sp]}')
        if self.MAP_HAS_PORTAL:
            lines.append(f'MAP.portal_data = {self.portal}')
        lines.append('MAP.map_data = \"\"\"')
        for y in range(self.shape[1] + 1):
            lines.append('    ' + ' '.join([self.map_data[(x, y)] for x in range(self.shape[0] + 1)]))
        lines.append('\"\"\"')
        if self.map_data_loop is not None:
            lines.append('MAP.map_data_loop = \"\"\"')
            for y in range(self.shape[1] + 1):
                lines.append('    ' + ' '.join([self.map_data_loop[(x, y)] for x in range(self.shape[0] + 1)]))
            lines.append('\"\"\"')
        lines.append('MAP.weight_data = \"\"\"')
        for y in range(self.shape[1] + 1):
            lines.append('    ' + ' '.join(['50'] * (self.shape[0] + 1)))
        lines.append('\"\"\"')
        if self.MAP_HAS_LAND_BASED:
            lines.append(f'MAP.land_based_data = {self.land_based}')
        lines.append('MAP.spawn_data = [')
        for battle in self.spawn_data:
            lines.append('    ' + str(battle) + ',')
        lines.append(']')
        if self.spawn_data_loop is not None:
            lines.append('MAP.spawn_data_loop = [')
            for battle in self.spawn_data_loop:
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
        lines.append('    # ===== Start of generated config =====')
        if len(self.MAP_SIREN_TEMPLATE):
            lines.append(f'    MAP_SIREN_TEMPLATE = {self.MAP_SIREN_TEMPLATE}')
            lines.append(f'    MOVABLE_ENEMY_TURN = {tuple(self.MOVABLE_ENEMY_TURN)}')
            lines.append(f'    MAP_HAS_SIREN = True')
            lines.append(f'    MAP_HAS_MOVABLE_ENEMY = {self.MAP_HAS_MOVABLE_ENEMY}')
        lines.append(f'    MAP_HAS_MAP_STORY = {self.MAP_HAS_MAP_STORY}')
        lines.append(f'    MAP_HAS_FLEET_STEP = {self.MAP_HAS_FLEET_STEP}')
        lines.append(f'    MAP_HAS_AMBUSH = {self.MAP_HAS_AMBUSH}')
        lines.append(f'    MAP_HAS_MYSTERY = {self.MAP_HAS_MYSTERY}')
        if self.MAP_HAS_PORTAL:
            lines.append(f'    MAP_HAS_PORTAL = {self.MAP_HAS_PORTAL}')
        if self.MAP_HAS_LAND_BASED:
            lines.append(f'    MAP_HAS_LAND_BASED = {self.MAP_HAS_LAND_BASED}')
        for n in range(1, 4):
            if self.__getattribute__(f'STAR_REQUIRE_{n}') != n:
                lines.append(f'    STAR_REQUIRE_{n} = 0')
        lines.append('    # ===== End of generated config =====')
        lines.append('')
        lines.append('')

        # Campaign
        battle = self.data["boss_refresh"]
        lines.append('class Campaign(CampaignBase):')
        lines.append('    MAP = MAP')
        lines.append(f'    ENEMY_FILTER = \'{ENEMY_FILTER}\'')
        lines.append('')
        lines.append('    def battle_0(self):')
        if len(self.MAP_SIREN_TEMPLATE):
            lines.append('        if self.clear_siren():')
            lines.append('            return True')
        preserve = self.data["boss_refresh"] - 5 if battle >= 5 else 0
        lines.append(f'        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve={preserve}):')
        lines.append('            return True')
        lines.append('')
        lines.append('        return self.battle_default()')
        lines.append('')
        if battle >= 6:
            lines.append('    def battle_5(self):')
            if len(self.MAP_SIREN_TEMPLATE):
                lines.append('        if self.clear_siren():')
                lines.append('            return True')
            preserve = 0
            lines.append(f'        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve={preserve}):')
            lines.append('            return True')
            lines.append('')
            lines.append('        return self.battle_default()')
            lines.append('')
        lines.append(f'    def battle_{self.data["boss_refresh"]}(self):')
        if battle >= 5:
            lines.append('        return self.fleet_boss.clear_boss()')
        else:
            lines.append('        return self.clear_boss()')

        return lines

    def write(self, path):
        file = os.path.join(path, self.map_file_name())
        has_modified_campaign_base = os.path.exists(os.path.join(path, 'campaign_base.py'))
        if has_modified_campaign_base:
            print('Using existing campaign_base.py')
        if os.path.exists(file):
            if OVERWRITE:
                print(f'Delete file: {file}')
                os.remove(file)
            else:
                print(f'File exists: {file}')
                return False
        print(f'Extract: {file}')
        with open(file, 'w') as f:
            for text in self.get_file_lines(has_modified_campaign_base=has_modified_campaign_base):
                f.write(text + '\n')


class ChapterTemplate:
    def __init__(self):
        pass

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
        def is_extra(name):
            name = name.lower().replace('.', '')
            return name in ['extra', 'ex']

        print('<<< SEARCH MAP >>>')
        name = name.strip()
        name = int(name) if name.isdigit() else name
        print(f'Searching: {name}')
        if isinstance(name, str):
            maps = []
            for map_id, data in DATA.items():
                if not isinstance(map_id, int) or is_extra(data['chapter_name']):
                    continue
                if not re.search(name, data['name']):
                    continue
                data = MapData(data, DATA_LOOP.get(map_id, None))
                print(f'Found map: {data}')
                maps.append(data)
        else:
            data = MapData(DATA[name], DATA_LOOP.get(name, None))
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
            for map_id, data in DATA.items():
                if not isinstance(map_id, int) or is_extra(data['chapter_name']):
                    continue
                if get_event_id(data['id']) == event_id:
                    data = MapData(data, DATA_LOOP.get(map_id, None))
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
        print('Please confirm selected the correct maps before extracting.\n'
              'Input any key and press ENTER to continue')
        input()

        if not os.path.exists(folder):
            os.mkdir(folder)
        for data in maps:
            data.write(folder)


"""
This an auto-tool to extract map files used in Alas.

Git clone https://github.com/AzurLaneTools/AzurLaneLuaScripts, to get the decrypted scripts.
Arguments:
    FILE:            Path to your AzurLaneLuaScripts directory
    FOLDER:          Folder to save, './campaign/test'
    KEYWORD:         A keyword in map name, such as '短兵相接' (7-2, zh-CN), 'Counterattack!' (3-4, en-US)
                     Or map id, such as 702 (7-2), 1140017 (Iris of Light and Dark D2)
    SELECT:          True if select all maps in the same event
                     False if extract this map only
    OVERWRITE:       If overwrite existing files
    IS_WAR_ARCHIVES: True if retrieved map is to be
                     adapted for war_archives usage
"""
FILE = '../AzurLaneLuaScripts'
FOLDER = './campaign/test'
KEYWORD = ''
SELECT = True
OVERWRITE = True
IS_WAR_ARCHIVES = False
ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'

LOADER = LuaLoader(FILE, server='CN')
DATA = LOADER.load('./sharecfgdata/chapter_template.lua')
DATA_LOOP = LOADER.load('./sharecfgdata/chapter_template_loop.lua')
# MAP_EVENT_LIST = LOADER.load('./sharecfg/map_event_list.lua')
# MAP_EVENT_TEMPLATE = LOADER.load('./sharecfg/map_event_template.lua')
EXPECTATION_DATA = LOADER.load('./sharecfgdata/expedition_data_template.lua')

ct = ChapterTemplate()
ct.extract(ct.get_chapter_by_name(KEYWORD, select=SELECT), folder=FOLDER)
