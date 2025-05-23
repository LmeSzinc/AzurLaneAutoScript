from module.base.timer import Timer
from module.handler.enemy_searching import \
    EnemySearchingHandler as EnemySearchingHandler_
from module.logger import logger
from module.os.assets import MAP_GOTO_GLOBE_FOG
from module.os_handler.assets import AUTO_SEARCH_REWARD, IN_MAP, ORDER_ENTER


class EnemySearchingHandler(EnemySearchingHandler_):
    def is_in_map(self):
        if IN_MAP.match_luma(self.device.image, offset=(200, 5)):
            return True
        if self.match_template_color(MAP_GOTO_GLOBE_FOG, offset=(5, 5)):
            return True

        return False

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

            # End
            if timeout.reached():
                logger.warning('wait_os_map_buttons timeout, assume waited')
                break
            if self.appear(ORDER_ENTER, offset=(20, 20)):
                break

            # A game bug that AUTO_SEARCH_REWARD from the last cleared zone popups
            if self.appear_then_click(AUTO_SEARCH_REWARD, offset=(50, 50), interval=3):
                continue
