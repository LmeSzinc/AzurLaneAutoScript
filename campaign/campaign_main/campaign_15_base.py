from module.base.mask import Mask
from module.base.timer import Timer
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.handler.assets import STRATEGY_OPENED
from module.handler.strategy import MOB_MOVE_OFFSET
from module.logger import logger
from module.map.map_grids import SelectedGrids
from module.map.utils import location_ensure
from module.map_detection.grid import GridInfo
from module.map_detection.utils_assets import ASSETS

MASK_MAP_UI_W15 = Mask(file='./assets/mask/MASK_MAP_UI_W15.png')


class Config:
    # Ambushes can be avoid by having more DDs.
    MAP_WALK_TURNING_OPTIMIZE = False
    MAP_HAS_MYSTERY = False
    MAP_ENEMY_TEMPLATE = ['Light', 'Main', 'Carrier', 'CarrierSpecial']
    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (80, 255 - 33),
        'width': (0.9, 10),
        'prominence': 10,
        'distance': 35,
    }
    HOMO_CANNY_THRESHOLD = (50, 100)
    MAP_SWIPE_MULTIPLY = (0.993, 1.011)
    MAP_SWIPE_MULTIPLY_MINITOUCH = (0.960, 0.978)
    MAP_SWIPE_MULTIPLY_MAATOUCH = (0.932, 0.949)


class W15GridInfo(GridInfo):
    def merge(self, info, mode='normal'):
        # Consider boss as siren
        if info.is_boss:
            if not self.is_land and self.may_siren:
                self.is_siren = True
                self.enemy_scale = 0
                self.enemy_genre = ''
                return True

        return super().merge(info, mode=mode)


class CampaignBase(CampaignBase_):
    ENEMY_FILTER = '1T > 1L > 1E > 1M > 2T > 2L > 2E > 2M > 3T > 3L > 3E > 3M'

    def map_data_init(self, map_):
        super().map_data_init(map_)
        # Patch ui_mask, get rid of supporting fleet
        _ = ASSETS.ui_mask
        ASSETS.ui_mask = MASK_MAP_UI_W15.image

    map_has_mob_move = True

    def strategy_set_execute(self, formation_index=None, sub_view=None, sub_hunt=None):
        super().strategy_set_execute(
            formation_index=formation_index,
            sub_view=sub_view,
            sub_hunt=sub_hunt,
        )
        logger.attr("Map has mob move", self.strategy_has_mob_move())

    def _map_swipe(self, vector, box=(239, 159, 1175, 628)):
        # Left border to 239, avoid swiping on support fleet
        return super()._map_swipe(vector, box=box)

    def mob_movable(self, location, target):
        """
        Check if mob is movable from location to target.
        This requires that:
            1. both location and target are grids in the map (not exceeding the boundaries)
            2. Manhattan distance between location and target is 1.
            3. location is a mob fleet
            4. target is a sea grid
        
        Args:
            location (tuple): Location of mob.
            target (tuple): Destination.
        
        Returns:
            bool: if movable.
        """
        location = location_ensure(location)
        target = location_ensure(target)
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
        Move mob from location to target, and confirm if successfully moved.

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

        view_target = SelectedGrids([self.map[location], self.map[target]]) \
            .sort_by_camera_distance(self.camera)[1]
        self.in_sight(view_target)
        origin_grid = self.convert_global_to_local(location)
        origin_grid.__str__ = location
        target_grid = self.convert_global_to_local(target)
        target_grid.__str__ = target

        logger.info('Select mob to move')
        skip_first_screenshot = True
        interval = Timer(2, count=4)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_in_strategy_mob_move():
                self.view.update(image=self.device.image)
            if origin_grid.predict_mob_move_icon():
                break
            # Click
            if interval.reached() and self.is_in_strategy_mob_move():
                self.device.click(origin_grid)
                interval.reset()
                continue

        logger.info('Select target grid')
        skip_first_screenshot = True
        interval = Timer(2, count=4)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(STRATEGY_OPENED, offset=MOB_MOVE_OFFSET):
                break
            # Click
            if interval.reached() and self.is_in_strategy_mob_move():
                self.device.click(target_grid)
                interval.reset()
                continue
            if self.handle_popup_confirm('MOB_MOVE'):
                continue

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
        self.map[target].may_enemy = True
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
        if not self.mob_movable(location, target):
            return False

        self.strategy_open()
        if not self.strategy_has_mob_move():
            logger.warning(f'No remain mob move trials, will abandon moving')
            self.strategy_close()
            return False
        self.strategy_mob_move_enter()
        self._mob_move(location, target)
        self.strategy_close(skip_first_screenshot=False)

        self._mob_move_info_change(location, target)
        self.find_path_initial()
        self.map.show()
