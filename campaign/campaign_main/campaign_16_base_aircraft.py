from module.base.decorator import del_cached_property
from module.base.timer import Timer
from module.base.utils import red_overlay_transparency, get_color
from module.handler.assets import MAP_AIR_STRIKE, STRATEGY_OPENED, AIR_STRIKE_CONFIRM
from module.handler.strategy import AIR_STRIKE_OFFSET
from module.logger import logger
from module.map.utils import location_ensure

from .campaign_support_fleet import CampaignBase as CampaignBase_


class Config:
    MAP_WALK_TURNING_OPTIMIZE = False
    MAP_HAS_MYSTERY = False
    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (80, 255 - 33),
        'prominence': 10,
        'distance': 35,
    }
    HOMO_CANNY_THRESHOLD = (50, 100)


class CampaignBase(CampaignBase_):
    MAP_AIR_STRIKE_OVERLAY_TRANSPARENCY_THRESHOLD = 0.35
    ENEMY_FILTER = '1L > 1M > 1E > 2L > 3L > 2M > 2E > 1C > 2C > 3M > 3E > 3C'

    def _air_strike_appear(self):
        return red_overlay_transparency(MAP_AIR_STRIKE.color, get_color(self.device.image, MAP_AIR_STRIKE.area)) > \
               self.MAP_AIR_STRIKE_OVERLAY_TRANSPARENCY_THRESHOLD

    def _air_strike(self, location):
        self.in_sight(location)
        attack_grid = self.convert_global_to_local(location)
        attack_grid.__str__ = location

        logger.info('Select grid to air strike')
        skip_first_screenshot = True
        interval = Timer(5, count=10)
        for _ in self.loop(skip_first=skip_first_screenshot):
            # End
            if self.is_in_strategy_air_strike():
                self.view.update(image=self.device.image)
                del_cached_property(attack_grid, "image_trans")
            if attack_grid.predict_air_strike_icon():
                break
            # Click
            if interval.reached() and self.is_in_strategy_air_strike():
                self.device.click(attack_grid)
                interval.reset()
                continue

        logger.info('Confirm air strike')
        skip_first_screenshot = True
        interval = Timer(3, count=6)
        MAP_AIR_STRIKE.load_color(self.device.image)
        for _ in self.loop(skip_first=skip_first_screenshot):
            if self._air_strike_appear():
                interval.reset()
                continue
            # End
            if self.appear(STRATEGY_OPENED, offset=AIR_STRIKE_OFFSET):
                break
            # Click
            if interval.reached() and self.is_in_strategy_air_strike():
                self.device.click(AIR_STRIKE_CONFIRM)
                interval.reset()
                continue

    def air_strike(self, location):
        """
        Open strategy, air strike on location, close strategy.

        Air strike at location X = (x, y) will hit range [x-2, y-1, x+2, y] as follows:

            OOOOO
            OOXOO

        Args:
            location (typle, str, GridInfo): Location of air strike
        """
        location = location_ensure(location)
        if self.map[location].is_land:
            logger.warning(f'Air strike location {location} is on land, will abandon attacking')
            return False
        self.strategy_open()
        if not self.strategy_has_air_strike():
            logger.warning(f'No remain air strike trials, will abandon attacking')
            self.strategy_close()
            return False
        self.strategy_air_strike_enter()
        self._air_strike(location)
        self.strategy_close(skip_first_screenshot=False)
        return True
