from module.base.timer import Timer
from module.base.utils import color_bar_percentage
from module.handler.assets import *
from module.handler.auto_search import AutoSearchHandler
from module.logger import logger
from module.ui.switch import Switch

fast_forward = Switch('Fast_Forward')
fast_forward.add_status('on', check_button=FAST_FORWARD_ON)
fast_forward.add_status('off', check_button=FAST_FORWARD_OFF)
fleet_lock = Switch('Fleet_Lock', offset=(5, 5))
fleet_lock.add_status('on', check_button=FLEET_LOCKED)
fleet_lock.add_status('off', check_button=FLEET_UNLOCKED)
auto_search = Switch('Auto_Search', offset=(20, 20))
auto_search.add_status('on', check_button=AUTO_SEARCH_ON)
auto_search.add_status('off', check_button=AUTO_SEARCH_OFF)


class FastForwardHandler(AutoSearchHandler):
    map_clear_percentage = 0.
    map_achieved_star_1 = False
    map_achieved_star_2 = False
    map_achieved_star_3 = False
    map_is_clear = False
    map_is_3_star = False
    map_is_green = False
    map_has_fast_forward = False
    map_is_clear_mode = False  # Clear mode == fast forward
    map_is_auto_search = False
    map_is_2x_book = False

    def map_get_info(self):
        """
        Logs:
            | INFO | [Map_info] 98%, star_1, star_2, star_3, clear, 3_star, green, fast_forward
        """
        self.map_clear_percentage = self.get_map_clear_percentage()
        self.map_achieved_star_1 = self.appear(MAP_STAR_1)
        self.map_achieved_star_2 = self.appear(MAP_STAR_2)
        self.map_achieved_star_3 = self.appear(MAP_STAR_3)
        self.map_is_clear = self.map_clear_percentage > 0.95
        self.map_is_3_star = self.map_achieved_star_1 and self.map_achieved_star_2 and self.map_achieved_star_3
        self.map_is_green = self.appear(MAP_GREEN)
        self.map_has_fast_forward = self.map_is_clear and fast_forward.appear(main=self)

        # Override config
        if self.map_achieved_star_1:
            # Story before boss spawn, Attribute "story_refresh_boss" in chapter_template.lua
            self.config.MAP_HAS_MAP_STORY = False
        self.config.MAP_CLEAR_ALL_THIS_TIME = self.config.STAR_REQUIRE_3 \
            and not self.__getattribute__(f'map_achieved_star_{self.config.STAR_REQUIRE_3}') \
            and (self.config.STOP_IF_MAP_REACH in ['map_3_star', 'map_green'])
        logger.attr('MAP_CLEAR_ALL_THIS_TIME', self.config.MAP_CLEAR_ALL_THIS_TIME)

        # Log
        names = ['map_achieved_star_1', 'map_achieved_star_2', 'map_achieved_star_3', 'map_is_clear', 'map_is_3_star',
                 'map_is_green', 'map_has_fast_forward']
        strip = ['map', 'achieved', 'is', 'has']
        log_names = ['_'.join([x for x in name.split('_') if x not in strip]) for name in names]
        text = ', '.join([l for l, n in zip(log_names, names) if self.__getattribute__(n)])
        text = f'{int(self.map_clear_percentage * 100)}%, ' + text
        logger.attr('Map_info', text)
        logger.attr('STOP_IF_MAP_REACH', self.config.STOP_IF_MAP_REACH)

    def handle_fast_forward(self):
        if not self.map_has_fast_forward:
            self.map_is_clear_mode = False
            self.map_is_auto_search = False
            self.map_is_2x_book = False
            return False

        if self.config.ENABLE_FAST_FORWARD:
            self.config.MAP_HAS_AMBUSH = False
            self.config.MAP_HAS_FLEET_STEP = False
            self.config.MAP_HAS_MOVABLE_ENEMY = False
            self.config.MAP_HAS_MOVABLE_NORMAL_ENEMY = False
            self.config.MAP_HAS_PORTAL = False
            self.config.MAP_HAS_LAND_BASED = False
            self.config.MAP_HAS_MAZE = False
            self.map_is_clear_mode = True
            self.map_is_auto_search = self.config.ENABLE_AUTO_SEARCH
            self.map_is_2x_book = self.config.ENABLE_2X_BOOK
        else:
            # When disable fast forward, MAP_HAS_AMBUSH depends on map settings.
            # self.config.MAP_HAS_AMBUSH = True
            self.map_is_clear_mode = False
            self.map_is_auto_search = False
            self.map_is_2x_book = False
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

    def handle_auto_search(self):
        """
        Returns:
            bool: If changed

        Pages:
            in: MAP_PREPARATION
        """
        # if not self.map_is_clear_mode:
        #     return False

        if not auto_search.appear(main=self):
            logger.info('No auto search option.')
            self.map_is_auto_search = False
            return False

        status = 'on' if self.map_is_auto_search else 'off'
        changed = auto_search.set(status=status, main=self)

        return changed

    def handle_auto_search_setting(self):
        """
        Returns:
            bool: If changed

        Pages:
            in: FLEET_PREPARATION
        """
        if not self.map_is_auto_search:
            return False

        self.fleet_preparation_sidebar_ensure(3)
        self.auto_search_setting_ensure(self.config.AUTO_SEARCH_SETTING)
        return True

    def handle_auto_search_continue(self):
        """
        Override AutoSearchHandler definition
        for 2x book handling if needed
        """
        if self.appear(AUTO_SEARCH_MENU_CONTINUE, offset=(20, 20), interval=2):
            self.map_is_2x_book = self.config.ENABLE_2X_BOOK
            self.handle_2x_book_setting(mode='auto')
            self.device.click(AUTO_SEARCH_MENU_CONTINUE)
            self.interval_reset(AUTO_SEARCH_MENU_CONTINUE)
            return True
        return False

    def get_map_clear_percentage(self):
        """
        Returns:
            float: 0 to 1.

        Pages:
            in: MAP_PREPARATION
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

    def _set_2x_book_status(self, status, check_button, box_button, skip_first_screenshot=True):
        """
        Set appropriate 2x book setting
        with corresponding status and buttons
        Built with retry mechanism that limits to 3
        attempts that span 3 second intervals each

        Args:
            status (string):
                on or off
            check_button (Button):
                button to check before attempting to click
            box_button (Button):
                button to click and image color count against
            skip_first_screenshot (bool):
                namesake

        Returns:
            bool:
                True if detected having set correctly
                False can occur for 2 reasons either
                assets insufficient to detect properly
                or 2x book setting is absent

        """
        clicked_timeout = Timer(3, count=6)
        clicked_threshold = 3
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if clicked_threshold < 0:
                break

            if clicked_timeout.reached():
                if self.appear(check_button, offset=(100, 50)):
                    enabled = self.image_color_count(box_button, color=(156, 255, 82), threshold=221, count=20)
                    if (status == 'on' and enabled) or (status == 'off' and not enabled):
                        return True
                    if (status == 'on' and not enabled) or (status == 'off' and enabled):
                        self.device.click(box_button)

                clicked_timeout.reset()
                clicked_threshold -= 1

        logger.warning(f'Wait time has expired; Cannot set 2x book setting')
        return False

    def handle_2x_book_setting(self, mode='prep'):
        """
        Handles 2x book setting if applicable

        Args:
            mode (string):
                prep or auto, assume auto if not prep

        Returns:
            bool:
                If handled to completion
        """
        if not hasattr(self, 'emotion'):
            logger.info('Emotion instance not loaded, cannot handle 2x book setting')
            return False

        logger.info(f'Handling 2x book setting, mode={mode}.')
        if mode == 'prep':
            book_check = BOOK_CHECK_PREP
            book_box = BOOK_BOX_PREP
        else:
            book_check = BOOK_CHECK_AUTO
            book_box = BOOK_BOX_AUTO

        status = 'on' if self.map_is_2x_book else 'off'
        if self._set_2x_book_status(status, book_check, book_box):
            self.emotion.map_is_2x_book = self.map_is_2x_book
        else:
            self.map_is_2x_book = False
            self.emotion.map_is_2x_book = self.map_is_2x_book

        self.handle_info_bar()
        return True
