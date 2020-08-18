from module.base.base import ModuleBase
from module.base.switch import Switch
from module.base.utils import color_bar_percentage
from module.handler.assets import *
from module.logger import logger

fast_forward = Switch('Fast_Forward')
fast_forward.add_status('on', check_button=FAST_FORWARD_ON)
fast_forward.add_status('off', check_button=FAST_FORWARD_OFF)
fleet_lock = Switch('Fleet_Lock')
fleet_lock.add_status('on', check_button=FLEET_LOCKED, offset=(5, 5))
fleet_lock.add_status('off', check_button=FLEET_UNLOCKED, offset=(5, 5))


class FastForwardHandler(ModuleBase):
    map_clear_percentage = 0.
    map_achieved_star_1 = False
    map_achieved_star_2 = False
    map_achieved_star_3 = False
    map_is_clear = False
    map_is_3_star = False
    map_is_green = False
    map_has_fast_forward = False

    map_clear_record = None

    def map_get_info(self):
        """
        Logs:
            | INFO | [Map_info] 98%, star_1, star_2, star_3, clear, 3_star, green, fast_forward
        """
        self.map_clear_percentage = color_bar_percentage(
            self.device.image, area=MAP_CLEAR_PERCENTAGE.area, prev_color=(231, 170, 82))
        self.map_achieved_star_1 = self.appear(MAP_STAR_1)
        self.map_achieved_star_2 = self.appear(MAP_STAR_2)
        self.map_achieved_star_3 = self.appear(MAP_STAR_3)
        self.map_is_clear = self.map_clear_percentage > 0.95
        self.map_is_3_star = self.map_achieved_star_1 and self.map_achieved_star_2 and self.map_achieved_star_3
        self.map_is_green = self.appear(MAP_GREEN)
        self.map_has_fast_forward = self.map_is_3_star and self.map_is_green and fast_forward.appear(main=self)

        # Override config
        if self.map_achieved_star_1:
            # Story before boss spawn, Attribute "story_refresh_boss" in chapter_template.lua
            self.config.MAP_HAS_MAP_STORY = False
        self.config.MAP_CLEAR_ALL_THIS_TIME = self.config.STAR_REQUIRE_3 \
            and not self.__getattribute__(f'map_achieved_star_{self.config.STAR_REQUIRE_3}') \
            and self.config.STOP_IF_MAP_REACH != 'map_green_without_3_star'
        logger.attr('MAP_CLEAR_ALL_THIS_TIME', self.config.MAP_CLEAR_ALL_THIS_TIME)

        # Log
        names = ['map_achieved_star_1', 'map_achieved_star_2', 'map_achieved_star_3', 'map_is_clear', 'map_is_3_star',
                 'map_is_green', 'map_has_fast_forward']
        strip = ['map', 'achieved', 'is', 'has']
        log_names = ['_'.join([x for x in name.split('_') if x not in strip]) for name in names]
        text = ', '.join([l for l, n in zip(log_names, names) if self.__getattribute__(n)])
        text = f'{int(self.map_clear_percentage * 100)}%, ' + text
        logger.attr('Map_info', text)

    def handle_fast_forward(self):
        if not self.map_has_fast_forward:
            return False

        if self.config.ENABLE_FAST_FORWARD:
            self.config.MAP_HAS_AMBUSH = False
            self.config.MAP_HAS_FLEET_STEP = False
            self.config.MAP_HAS_MOVABLE_ENEMY = False
        else:
            # When disable fast forward, MAP_HAS_AMBUSH depends on map settings.
            # self.config.MAP_HAS_AMBUSH = True
            pass

        status = 'on' if self.config.ENABLE_FAST_FORWARD else 'off'
        changed = fast_forward.set(status=status, main=self)
        return changed

    def handle_map_fleet_lock(self):
        # Fleet lock depends on if it appear on map, not depends on map status.
        # Because if already in map, there's no map status,
        if not fleet_lock.appear(main=self):
            logger.info('No fleet lock option.')
            return False

        status = 'on' if self.config.ENABLE_MAP_FLEET_LOCK else 'off'
        changed = fleet_lock.set(status=status, main=self)

        return changed

    def get_map_clear_percentage(self):
        """
        Returns:
            float: 0 to 1.
        """
        return color_bar_percentage(self.device.image, area=MAP_CLEAR_PERCENTAGE.area, prev_color=(231, 170, 82))

    def triggered_map_stop(self):
        """
        Returns:
            bool:
        """
        if self.config.STOP_IF_MAP_REACH == 'map_100':
            if self.map_is_clear:
                return True

        if self.config.STOP_IF_MAP_REACH == 'map_3_star':
            if self.map_is_clear and self.map_is_3_star:
                return True

        if self.config.STOP_IF_MAP_REACH == 'map_green_without_3_star':
            if self.map_is_clear and self.map_is_green:
                return True

        if self.config.STOP_IF_MAP_REACH == 'map_green':
            if self.map_is_clear and self.map_is_3_star and self.map_is_green:
                return True

        return False

    def handle_map_stop(self):
        if self.map_clear_record is True:
            return False

        flag = self.triggered_map_stop()
        if self.map_clear_record is None:
            self.map_clear_record = flag
        elif self.map_clear_record is False and flag:
            return True

        return False