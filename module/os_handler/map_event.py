from module.combat.assets import *
from module.handler.info_handler import InfoHandler
from module.os_handler.assets import *


class MapEventHandler(InfoHandler):
    def handle_map_get_items(self):
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
