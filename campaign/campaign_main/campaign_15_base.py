from module.base.mask import Mask
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.handler.assets import MOB_MOVE_ICON, STRATEGY_OPENED
from module.map_detection.utils_assets import ASSETS
from module.logger import logger
from module.map.utils import location_ensure

MASK_MAP_UI_W15 = Mask(file='./assets/mask/MASK_MAP_UI_W15.png')


class Config:
    # Disabled because having errors
    MAP_SWIPE_PREDICT_WITH_SEA_GRIDS = False
    # Ambushes can be avoid by having more DDs.
    MAP_WALK_OPTIMIZE = False
    MAP_ENEMY_TEMPLATE = ['Light', 'Main', 'Carrier', 'CarrierSpecial']


class CampaignBase(CampaignBase_):
    ENEMY_FILTER = '1T > 1L > 1E > 1M > 2T > 2L > 2E > 2M > 3T > 3L > 3E > 3M'

    def map_data_init(self, map_):
        super().map_data_init(map_)
        # Patch ui_mask, get rid of supporting fleet
        _ = ASSETS.ui_mask
        ASSETS.ui_mask = MASK_MAP_UI_W15.image

    def mob_movable(self, location, target):
        """
        Check if mob is movable from location to target.
        This requires that:
            0. both location and target are grids in the map (not exceeding the boundaries)
            1. Manhattan distance between location and target is 1.
            1. location is a mob fleet
            2. target is a sea grid
        
        Args:
            location (tuple): Location of mob.
            target (tuple): Destination.
        
        Returns:
            bool: if movable.
        """
        movable = True

        try:
            logger.info(f'location: {self.map[location]}, target: {self.map[target]}')
        except KeyError as e:
            logger.exception(f'Given coordinates are outside the map.')
            raise e

        if abs(location[0] - target[0]) + abs(location[1] - target[1]) != 1:
            logger.error(f'{self.map[target]} is not adjacent from {self.map[location]}.')
            movable = False

        if not self.map[location].is_enemy:
            logger.error(f'{self.map[location]} is not a mob fleet.')
            movable = False

        if not self.map[target].is_sea:
            logger.error(f'{self.map[target]} is not a sea grid.')
            movable = False
        
        if not movable:
            logger.error(f'Cannot move from {self.map[location]} to {self.map[target]}.')

        return movable
    
    def _mob_move(self, location, target):
        """
        Move mob from location to target.

        Args: 
            location (tuple, str, GridInfo): Location of mob.
            target (tuple, str, GridInfo): Destination.
        
        Returns:
            bool: If mob moved.
        
        Pages:
            in: MOB_MOVE_CANCEL
            out: STRATEGY_OPENED
        """
        location = location_ensure(location)
        target = location_ensure(target)

        movable = self.mob_movable(location, target)

        if not movable:
            self.strategy_mob_move_cancel()
            return False
        else:
            self.in_sight(location, sight=self._walk_sight)
            self.focus_to(location)
            self.focus_to_grid_center()
            grid = self.convert_global_to_local(location)
            grid.__str__ = location
            grid_2 = self.convert_global_to_local(target)
            grid_2.__str__ = target

            self.device.click(grid)
            while 1:
                self.device.screenshot()
                if self.appear(MOB_MOVE_ICON, offset=(80, 80)):
                    break
            self.device.click(grid_2)
            while 1:
                self.device.screenshot()
                if self.handle_popup_confirm('MOB_MOVE'):
                    continue

                if self.appear(STRATEGY_OPENED, offset=(120, 120)):
                    break
            return True

    def _mob_move_info_change(self, location, target):
        location = location_ensure(location)
        target = location_ensure(target)
        self.map[target].enemy_scale = self.map[location].enemy_scale
        self.map[location].enemy_scale = 0
        self.map[target].enemy_genre = self.map[location].enemy_genre
        self.map[location].enemy_genre = None
        self.map[target].is_boss = self.map[location].is_boss
        self.map[location].is_boss = False
        self.map[target].is_enemy = True
        self.map[location].is_enemy = False

    def mob_move(self, location, target):
        """
        Open strategy, move mob fleet from location to target, close strategy.

        Args:
            location (tuple, str, GridInfo): Location of mob.
            target (tuple, str, GridInfo): Destination.
            
        Returns:
            bool: If mob moved

        Pages:
            in: IN_MAP
            out: IN_MAP
        """
        self.strategy_open()
        remain = self.strategy_get_mob_move_remain()
        if remain == 0:
            logger.warning(f'No remain mob move trials, will abandon moving')
            self.strategy_close()
            return False
        self.strategy_mob_move_enter()
        result = self._mob_move(location, target)
        self.strategy_close(skip_first_screenshot=False)
        if result:
            self._mob_move_info_change(location, target)
        return result

