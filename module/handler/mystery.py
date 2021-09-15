from module.base.timer import Timer
from module.base.utils import area_in_area
from module.combat.assets import GET_ITEMS_1
from module.handler.assets import *
from module.handler.enemy_searching import EnemySearchingHandler
from module.handler.strategy import StrategyHandler
from module.logger import logger


class MysteryHandler(StrategyHandler, EnemySearchingHandler):
    _get_ammo_log_timer = Timer(3)
    carrier_count = 0

    def handle_mystery(self, button=None):
        """
        Args:
            button (optional): Button to click when get_items.
                Can be destination grid which makes the bot more like human.
        """
        if button is None or area_in_area(button.button, MYSTERY_ITEM.area, threshold=20):
            button = MYSTERY_ITEM

        with self.stat.new(
                genre=self.config.campaign_name, save=self.config.DropRecord_SaveCombat, upload=False
        ) as drop:
            if self.appear(GET_ITEMS_1):
                logger.attr('Mystery', 'Get item')
                drop.add(self.device.image)
                self.device.click(button)
                self.device.sleep(0.5)
                self.device.screenshot()
                self.strategy_close()
                return 'get_item'

            if self.info_bar_count():
                if self._get_ammo_log_timer.reached() and self.appear(GET_AMMO):
                    logger.attr('Mystery', 'Get ammo')
                    self._get_ammo_log_timer.reset()
                    drop.add(self.device.image)
                    return 'get_ammo'

            if self.config.MAP_MYSTERY_HAS_CARRIER:
                if self.is_in_map() and self.enemy_searching_appear():
                    logger.attr('Mystery', 'Get carrier')
                    self.carrier_count += 1
                    drop.add(self.device.image)
                    self.handle_in_map_with_enemy_searching()
                    return 'get_carrier'

            return False
