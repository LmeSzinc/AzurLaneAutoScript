from module.combat.assets import *
from module.handler.info_handler import InfoHandler
from module.os_handler.assets import *


class MapEventHandler(InfoHandler):
    def handle_map_get_items(self):
        if self.appear(GET_ITEMS_1) or self.appear(GET_ITEMS_2) or self.appear(GET_ITEMS_3):
            self.device.click(CLICK_SAFE_AREA)
            return True
        if self.appear(GET_OS_STATUS):
            self.device.click(CLICK_SAFE_AREA)
            return True

        return False

    def handle_map_archives(self):
        if self.appear(MAP_ARCHIVES, interval=5):
            self.device.click(CLICK_SAFE_AREA)
            return True

        return False
