from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.logger import logger

class Config:
    HOMO_EDGE_COLOR_RANGE = (0, 12)
    MAP_SWIPE_MULTIPLY = 1.537
    MAP_SWIPE_MULTIPLY_MINITOUCH = 1.486


class CampaignBase(CampaignBase_):
    ENEMY_FILTER = '1T > 1M > 1E > 1L > 2T > 2M > 2E > 2L > 3T > 3M > 3E > 3L'
    picked_light_house = []
    picked_flare = []

    def map_data_init(self, map_):
        super().map_data_init(map_)
        self.picked_light_house = []
        self.picked_flare = []

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
            self.clear_chosen_mystery(grid)
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
