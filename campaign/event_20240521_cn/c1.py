from campaign.event_20240521_cn.campaign_base import CurrentFleetGrid
from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap

MAP = CampaignMap('C1')
MAP.shape = 'I9'
MAP.camera_data = ['D3', 'D7', 'F3', 'F7']
MAP.camera_data_spawn_point = []
MAP.map_data = """
    -- -- ++ ++ ++ ++ ++ ++ ++
    -- ME ME ++ ++ ++ -- ME --
    ME -- -- ++ ++ ++ ME -- ME
    ++ -- -- ++ ++ ++ -- -- --
    ++ Me -- ++ ++ ++ -- ++ --
    -- -- -- -- -- -- -- Me --
    -- ++ ++ ++ MS __ Me ++ ++
    -- ME -- Me -- MS -- MB ++
    ME -- ++ -- Me ++ -- -- ME
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 2},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, \
A7, B7, C7, D7, E7, F7, G7, H7, I7, \
A8, B8, C8, D8, E8, F8, G8, H8, I8, \
A9, B9, C9, D9, E9, F9, G9, H9, I9, \
    = MAP.flatten()


class Config:
    # ===== Start of generated config =====
    MAP_SIREN_TEMPLATE = ['DD']
    MOVABLE_ENEMY_TURN = (2,)
    MAP_HAS_SIREN = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_MAP_STORY = True
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_MYSTERY = False
    # ===== End of generated config =====

    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (80, 255 - 33),
        'width': (0.9, 10),
        'prominence': 10,
        'distance': 35,
    }
    MAP_ENEMY_GENRE_DETECTION_SCALING = {
        'DD': 1.111,
        'CL': 1.111,
        'CA': 1.111,
        'CV': 1.111,
        'BB': 1.111,
    }
    MAP_SWIPE_MULTIPLY = (1.136, 1.158)
    MAP_SWIPE_MULTIPLY_MINITOUCH = (1.099, 1.119)
    MAP_SWIPE_MULTIPLY_MAATOUCH = (1.067, 1.086)
    MAP_ENSURE_EDGE_INSIGHT_CORNER = 'bottom'
    MAP_WALK_USE_CURRENT_FLEET = True


class Campaign(CampaignBase):
    MAP = MAP
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'
    grid_class = CurrentFleetGrid
    bored_visited_G3 = False
    bored_visited_H2 = False

    def find_current_fleet(self):
        logger.hr('Find current fleet')
        logger.info('No fleet scan, assume fleet_1 at D5')
        self.fleet_1 = D5.location
        if self.config.FLEET_2:
            logger.info('No fleet scan, assume fleet_2 at F5')
            self.fleet_2 = F5.location

    def map_init(self, map_):
        super().map_init(map_)
        self.bored_visited_G3 = False
        self.bored_visited_H2 = False
        # Only fleet_1
        self.config.FLEET_BOSS = 1

    def bored_visit(self):
        # Visit all grids covered
        if not self.bored_visited_G3:
            self.bored_visited_G3 = True
            if self.clear_chosen_enemy(G3):
                return True
        if not self.bored_visited_H2:
            self.bored_visited_H2 = True
            if self.clear_chosen_enemy(H2):
                return True
        return False

    def battle_function(self):
        if self.battle_count == 0:
            return self.battle_0()

        if self.config.MAP_CLEAR_ALL_THIS_TIME:
            # From
            #     @Config.when(MAP_CLEAR_ALL_THIS_TIME=True)
            #     def battle_function(self):
            remain = self.map.select(is_enemy=True) \
                .add(self.map.select(is_siren=True)) \
                .add(self.map.select(is_fortress=True)) \
                .delete(self.map.select(is_boss=True))
            logger.info(f'Enemy remain: {remain}')
            logger.info(f'bored_visited_G3: {self.bored_visited_G3}, bored_visited_H2: {self.bored_visited_H2}')
            if remain.count > 0:
                if self.clear_siren():
                    return True
                self.clear_mechanism()
                return self.battle_default()
            else:
                if self.bored_visit():
                    return True
                result = self.battle_boss()
                return result
        else:
            return super().battle_function()

    def battle_0(self):
        if self.fleet_step >= 3:
            if self.clear_chosen_enemy(E7, expected='siren'):
                return True
        else:
            self.goto(E6)
            if self.clear_chosen_enemy(E7, expected='siren'):
                return True

        logger.warning(f'A1.battle_0() did not cleared siren')
        return self.battle_default()

    def battle_1(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True

        return self.battle_default()

    def battle_4(self):
        return self.clear_boss()
