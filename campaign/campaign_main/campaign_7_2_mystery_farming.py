from campaign.campaign_main.campaign_7_2 import MAP
from campaign.campaign_main.campaign_7_2 import Config as ConfigBase
from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

# MAP.in_map_swipe_preset_data = (-1, 0)

A1, B1, C1, D1, E1, F1, G1, H1, \
A2, B2, C2, D2, E2, F2, G2, H2, \
A3, B3, C3, D3, E3, F3, G3, H3, \
A4, B4, C4, D4, E4, F4, G4, H4, \
A5, B5, C5, D5, E5, F5, G5, H5 = MAP.flatten()

ROAD_MAIN = RoadGrids([A3, [C3, B4, C5], [F1, G2, G3]])
GRIDS_FOR_FASTER = SelectedGrids([A3, C3, E3, G3])
FLEET_2_STEP_ON = SelectedGrids([A3, G3, C3, E3])


class Config(ConfigBase):
    ENABLE_AUTO_SEARCH = False


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.config.C72MysteryFarming_StepOnA3:
            if self.fleet_2_step_on(FLEET_2_STEP_ON, roadblocks=[ROAD_MAIN]):
                return True

            ignore = None
            if self.fleet_at(A3, fleet=2) and A1.enemy_scale != 3 and not self.fleet_at(A1, fleet=1):
                ignore = SelectedGrids([A2])
            if self.fleet_at(G3, fleet=2):
                ignore = SelectedGrids([H3])

            self.clear_all_mystery(nearby=False, ignore=ignore)
        else:
            self.clear_all_mystery(nearby=False)

        if self.clear_roadblocks([ROAD_MAIN], strongest=True):
            return True
        if self.clear_potential_roadblocks([ROAD_MAIN], strongest=True):
            return True

        if self.clear_enemy(scale=(3,)):
            return True

        if self.clear_grids_for_faster(GRIDS_FOR_FASTER, scale=(2,)):
            return True
        if self.clear_enemy(scale=(2,)):
            return True
        if self.clear_grids_for_faster(GRIDS_FOR_FASTER):
            return True

        return self.battle_default()

    def battle_3(self):
        if self.config.C72MysteryFarming_StepOnA3:
            ignore = None
            if self.fleet_at(A3, fleet=2):
                ignore = SelectedGrids([A2])
            if self.fleet_at(G3, fleet=2):
                ignore = SelectedGrids([H3])
            self.clear_all_mystery(nearby=False, ignore=ignore)

            if self.fleet_at(A3, fleet=2) and A2.is_mystery:
                self.fleet_2.clear_chosen_mystery(A2)
            if self.fleet_at(G3, fleet=2) and H3.is_mystery:
                self.fleet_2.clear_chosen_mystery(H3)
        else:
            self.clear_all_mystery(nearby=False)

        if self.map.select(is_mystery=True, is_accessible=False):
            logger.info('Roadblock blocks mystery.')
            if self.fleet_1.clear_roadblocks([ROAD_MAIN]):
                return True

        if not self.map.select(is_mystery=True):
            self.withdraw()

    @property
    def _map_battle(self):
        return 3
