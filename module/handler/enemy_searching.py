from module.base.timer import Timer
from module.base.utils import red_overlay_transparency, get_color
from module.handler.assets import *
from module.handler.info_bar import InfoBarHandler
from module.logger import logger


class EnemySearchingHandler(InfoBarHandler):
    MAP_ENEMY_SEARCHING_OVERLAY_TRANSPARENCY_THRESHOLD = 0.5  # Usually (0.70, 0.80).
    MAP_ENEMY_SEARCHING_TIMEOUT_SECOND = 4.5

    def enemy_searching_color_initial(self):
        MAP_ENEMY_SEARCHING.load_color(self.device.image)

    def enemy_searching_appear(self):
        return red_overlay_transparency(
            MAP_ENEMY_SEARCHING.color, get_color(self.device.image, MAP_ENEMY_SEARCHING.area)
        ) > self.MAP_ENEMY_SEARCHING_OVERLAY_TRANSPARENCY_THRESHOLD

    def handle_enemy_flashing(self):
        self.device.sleep(1.2)

    def handle_in_stage(self):
        if self.appear(IN_STAGE_RED) or self.appear(IN_STAGE_BLUE):
            logger.info('In stage.')
            # self.device.sleep(0.5)
            self.ensure_no_info_bar(timeout=0.6)
            return True
        else:
            return False

    def is_in_map(self):
        return self.appear(IN_MAP)

    def handle_in_map_with_enemy_searching(self):
        if not self.is_in_map():
            return False

        timeout = Timer(self.MAP_ENEMY_SEARCHING_TIMEOUT_SECOND)
        appeared = False
        while 1:
            timeout.start()
            if self.enemy_searching_appear():
                appeared = True
            else:
                if appeared:
                    self.handle_enemy_flashing()
                    self.device.sleep(0.3)
                    logger.info('In map.')
                    break
                self.enemy_searching_color_initial()

            if timeout.reached():
                # logger.warning('Enemy searching timeout.')
                logger.info('Enemy searching timeout.')
                break

            self.device.screenshot()
        return True

    def handle_in_map(self):
        if not self.is_in_map():
            return False

        self.device.sleep((1, 1.2))
        return True
