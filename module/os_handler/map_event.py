from module.base.timer import Timer
from module.combat.assets import *
from module.handler.assets import *
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

    def handle_map_event(self):
        if self.handle_map_get_items():
            return True
        if self.handle_map_archives():
            return True
        if self.handle_guild_popup_cancel():
            return True
        if self.handle_ash_popup():
            return True
        if self.handle_story_skip():
            return True

        return False

    def ensure_no_map_event(self, timeout=1.5):
        confirm_timer = Timer(timeout, count=int(timeout / 0.5)).start()

        while 1:
            self.device.screenshot()

            if self.handle_map_event():
                confirm_timer.reset()
                continue
            if not self.is_in_map():
                confirm_timer.reset()
                continue

            if confirm_timer.reached():
                break
