from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.logger import logger


class Config:
    HOMO_EDGE_COLOR_RANGE = (0, 12)
    HOMO_EDGE_HOUGHLINES_THRESHOLD = 210
    MAP_SWIPE_MULTIPLY = (1.006, 1.025)
    MAP_SWIPE_MULTIPLY_MINITOUCH = (0.973, 0.991)
    MAP_SWIPE_MULTIPLY_MAATOUCH = (0.944, 0.961)

    # Disabled because having errors
    MAP_SWIPE_PREDICT_WITH_SEA_GRIDS = False
    # Ambushes can be avoid by having more DDs.
    MAP_WALK_TURNING_OPTIMIZE = False


class CampaignBase(CampaignBase_):
    ENEMY_FILTER = '1T > 1L > 1E > 1M > 2T > 2L > 2E > 2M > 3T > 3L > 3E > 3M'
    picked_light_house = []
    picked_flare = []

    def map_data_init(self, map_):
        super().map_data_init(map_)
        self.picked_light_house = []
        self.picked_flare = []

    def handle_mystery_items(self, button=None, drop=None):
        """
        Handle get flares, but not counted as mystery.
        """
        super().handle_mystery_items(button=button, drop=None)
        return False

    def pick_up_flare(self, grid):
        """
        Args:
            grid (GridInfo):

        Returns:
            bool: False
        """
        grid.is_flare = True
        if grid in self.picked_flare:
            logger.info(f'Flares {grid} already picked up')
        elif grid.is_accessible:
            logger.info(f'Pick up flares on {grid}')
            # get_items shows after flares picked up.
            self.goto(grid)
            self.picked_flare.append(grid)
        else:
            logger.info(f'Flares {grid} not accessible, will check in next battle')

        return False

    def pick_up_light_house(self, grid):
        """
        Args:
            grid (GridInfo):

        Returns:
            bool: False
        """
        if grid in self.picked_light_house:
            logger.info(f'Light house {grid} already picked up')
        elif grid.is_accessible:
            logger.info(f'Pick up light house on {grid}')
            self.goto(grid)
            self.picked_light_house.append(grid)
            self.ensure_no_info_bar()
        else:
            logger.info(f'Light house {grid} not accessible, will check in next battle')

        return False
