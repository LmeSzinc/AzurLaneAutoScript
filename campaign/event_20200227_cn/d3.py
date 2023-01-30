from module.campaign.assets import D3 as ENTRANCE
from module.campaign.campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('d3')
MAP.shape = 'H7'
MAP.map_data = '''
    MS -- ++ MB MB ++ -- MS
    -- ME ++ -- -- ++ ME --
    ME SP -- -- -- -- SP ME
    -- -- ME ME -- ME -- --
    -- ++ ++ ++ -- ME -- ++
    ME -- ME ME -- ++ ME ME
    -- ME -- ME MS -- ME --
'''
MAP.weight_data = '''
    10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10
'''
MAP.camera_data = ['D3', 'D5', 'E5']
# MAP.camera_data = ['D3', 'D5']
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 2},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 2, 'siren': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 2},
    {'battle': 5, 'enemy': 1},
    {'battle': 6, 'boss': 1},
]

A1, B1, C1, D1, E1, F1, G1, H1, \
A2, B2, C2, D2, E2, F2, G2, H2, \
A3, B3, C3, D3, E3, F3, G3, H3, \
A4, B4, C4, D4, E4, F4, G4, H4, \
A5, B5, C5, D5, E5, F5, G5, H5, \
A6, B6, C6, D6, E6, F6, G6, H6, \
A7, B7, C7, D7, E7, F7, G7, H7, \
    = MAP.flatten()

ROAD_MAIN = RoadGrids([[A3, B2], [G2, H3]])


class Config:
    MAP_HAS_AMBUSH = False
    CAMPAIGN_MODE = 'cd'


class Campaign(CampaignBase):
    ENTRANCE = ENTRANCE
    MAP = MAP

    def battle_0(self):
        if self.clear_roadblocks([ROAD_MAIN]):
            return True
        if self.clear_siren():
            return True

        if self.clear_enemy(scale=(3,)):
            return True
        return self.battle_default()

    battle_1 = battle_0
    battle_2 = battle_0

    def battle_3(self):
        if self.clear_enemy(strongest=True):
            return True

        return self.battle_default()

    battle_4 = battle_3

    def battle_5(self):
        if self.clear_enemy(scale=(2, 1)):
            return True

        return self.battle_default()

    def battle_6(self):
        return self.fleet_boss.clear_boss()
