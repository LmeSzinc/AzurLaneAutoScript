from module.base.timer import Timer
from module.combat.assets import *
from module.handler.assets import *
from module.logger import logger
from module.os_handler.assets import *
from module.os_handler.enemy_searching import EnemySearchingHandler


class MapEventHandler(EnemySearchingHandler):
    def handle_map_get_items(self):
        if self.is_in_map():
            return False

        if self.appear(GET_ITEMS_1, interval=2) \
                or self.appear(GET_ITEMS_2, interval=2) \
                or self.appear(GET_ITEMS_3, interval=2):
            self.device.click(CLICK_SAFE_AREA)
            return True
        if self.appear(GET_ADAPTABILITY, interval=2):
            self.device.click(CLICK_SAFE_AREA)
            return True
        if self.appear(GET_MEOWFFICER_ITEMS_1, interval=2):
            self.device.click(CLICK_SAFE_AREA)
            return True
        if self.appear(GET_MEOWFFICER_ITEMS_2, interval=2):
            self.device.click(CLICK_SAFE_AREA)
            return True

        return False

    def handle_map_archives(self):
        if self.appear(MAP_ARCHIVES, interval=5):
            self.device.click(CLICK_SAFE_AREA)
            return True
        if self.appear_then_click(MAP_WORLD, offset=(20, 20), interval=5):
            return True

        return False

    def handle_ash_popup(self):
        name = 'ASH'
        if self.appear(POPUP_CONFIRM, offset=self._popup_offset) \
                and self.appear(POPUP_CANCEL, offset=self._popup_offset, interval=2) \
                and self.image_color_count(ASH_POPUP_CHECK, color=(255, 93, 90), threshold=221, count=100):
            POPUP_CANCEL.name = POPUP_CANCEL.name + '_' + name
            self.device.click(POPUP_CANCEL)
            POPUP_CANCEL.name = POPUP_CANCEL.name[:-len(name) - 1]
            return True
        else:
            return False

    def handle_siren_platform(self):
        """
        Handle siren platform notice after entering map

        Returns:
            bool: If handled
        """
        if not self.handle_story_skip():
            return False

        logger.info('Handle siren platform')
        timeout = Timer(self.MAP_ENEMY_SEARCHING_TIMEOUT_SECOND).start()
        appeared = False
        while 1:
            self.device.screenshot()
            if self.is_in_map():
                timeout.start()
            else:
                timeout.reset()

            if self.handle_story_skip():
                timeout.reset()
                continue

            # End
            if self.enemy_searching_appear():
                appeared = True
            else:
                if appeared:
                    self.handle_enemy_flashing()
                    self.device.sleep(1)
                    logger.info('Enemy searching appeared.')
                    break
                self.enemy_searching_color_initial()
            if timeout.reached():
                logger.info('Enemy searching timeout.')
                break

        return True

    def handle_map_event(self):
        """
        Returns:
            bool: If clicked to handle any map event.
        """
        if self.handle_map_get_items():
            return True
        if self.handle_map_archives():
            return True
        if self.handle_guild_popup_cancel():
            return True
        if self.handle_ash_popup():
            return True
        if self.handle_urgent_commission(save_get_items=False):
            return True
        if self.handle_story_skip():
            return True

        return False

    _os_in_map_confirm_timer = Timer(1.5, count=3)

    def handle_os_in_map(self):
        """
        Returns:
            bool: If is in map and confirmed.
        """
        if self.is_in_map():
            if self._os_in_map_confirm_timer.reached():
                return True
            else:
                return False
        else:
            self._os_in_map_confirm_timer.reset()
            return False

    def ensure_no_map_event(self):
        self._os_in_map_confirm_timer.reset()

        while 1:
            self.device.screenshot()

            if self.handle_map_event():
                continue

            # End
            if self.handle_os_in_map():
                break
