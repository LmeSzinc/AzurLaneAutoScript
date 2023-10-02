from module.base.timer import Timer
from module.logger import logger
from tasks.base.assets.assets_base_page import CLOSE
from tasks.base.assets.assets_base_popup import GET_REWARD
from tasks.item.assets.assets_item_relics import *
from tasks.item.keywords import KEYWORD_ITEM_TAB
from tasks.item.ui import ItemUI


class RelicsUI(ItemUI):
    def _is_in_salvage(self) -> bool:
        return self.appear(ORDER_ASCENDING) or self.appear(ORDER_DESCENDING)

    def salvage_relic(self, skip_first_screenshot=True) -> bool:
        logger.hr('Salvage Relic', level=2)
        self.item_goto(KEYWORD_ITEM_TAB.Relics, wait_until_stable=False)
        while 1:  # relic tab -> salvage
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._is_in_salvage():
                logger.info('_is_in_salvage')
                break
            if self.appear_then_click(GOTO_SALVAGE, interval=2):
                continue

        skip_first_screenshot = True
        interval = Timer(1)
        timeout = Timer(5, count=3).start()
        while 1:  # salvage -> first relic selected
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Timeout when selecting first relic')
                return False
            # The first frame entering relic page, SALVAGE is a white button as it's the default state.
            # At the second frame, SALVAGE is disabled since no items are selected.
            # So here uses the minus button on the first relic.
            if self.image_color_count(FIRST_RELIC_SELECTED, color=(245, 245, 245), threshold=221, count=300):
                logger.info('First relic selected')
                break
            if self.appear_then_click(ORDER_DESCENDING, interval=2):
                continue
            if interval.reached() and self.appear(ORDER_ASCENDING) \
                    and self.image_color_count(FIRST_RELIC, (233, 192, 108)):
                self.device.click(FIRST_RELIC)
                interval.reset()
                continue

        skip_first_screenshot = True
        while 1:  # selected -> rewards claimed
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(GET_REWARD):
                logger.info("Relic salvaged")
                break
            if self.appear_then_click(SALVAGE, interval=2):
                continue
            if self.handle_popup_confirm():
                continue

        skip_first_screenshot = True
        interval = Timer(1)
        while 1:  # rewards claimed -> relic tab page
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(GOTO_SALVAGE):
                logger.info("Salvage page exited")
                break
            if self.handle_reward(interval=2):
                continue
            if interval.reached() and self._is_in_salvage():
                logger.info(f'_is_in_salvage -> {CLOSE}')
                self.device.click(CLOSE)
                interval.reset()
                continue
        return True
