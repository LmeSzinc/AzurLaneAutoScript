from module.base.timer import Timer
from module.handler.enemy_searching import \
    EnemySearchingHandler as EnemySearchingHandler_
from module.logger import logger
from module.os.assets import MAP_GOTO_GLOBE_FOG
from module.os_handler.assets import IN_MAP, ORDER_ENTER


class EnemySearchingHandler(EnemySearchingHandler_):
    def is_in_map(self):
        return self.appear(IN_MAP, offset=(200, 5)) or \
               self.appear(MAP_GOTO_GLOBE_FOG, offset=(5, 5))

    def wait_os_map_buttons(self, skip_first_screenshot=True):
        """
        When entering a os map, radar and buttons slide out from the right.
        Wait until they slide to the final position.
        """
        timeout = Timer(1, count=2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('wait_os_map_buttons timeout, assume waited')
                break
            if self.appear(ORDER_ENTER, offset=(20, 20)):
                break
