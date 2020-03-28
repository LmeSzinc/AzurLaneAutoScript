from module.base.timer import Timer
from module.base.utils import area_in_area
from module.handler.assets import *
from module.handler.strategy import StrategyHandler
from module.logger import logger


class MysteryHandler(StrategyHandler):
    _get_ammo_log_timer = Timer(3)

    def handle_mystery(self, button=None):
        """
        Args:
            button (optional): Button to click when get_items.
                Can be destination grid which makes the bot more like human.
        """
        if button is None or area_in_area(button.button, MYSTERY_ITEM.area, threshold=20):
            button = GET_ITEMS_1

        if self.appear(GET_ITEMS_1):
            logger.attr('Mystery', 'Get item')
            self._save_mystery_image()
            self.device.click(button)
            self.device.sleep(0.5)
            self.device.screenshot()
            self.handle_opened_strategy_bar()
            return True

        if self.info_bar_count():
            if self._get_ammo_log_timer.reached() and self.appear(GET_AMMO):
                logger.attr('Mystery', 'Get ammo')
                self._get_ammo_log_timer.reset()
                self._save_mystery_image()

                return True

        # if self.handle_info_bar():
        #     return True

        return False

    def _save_mystery_image(self):
        if self.config.ENABLE_SAVE_GET_ITEMS:
            self.device.save_screenshot('mystery')
