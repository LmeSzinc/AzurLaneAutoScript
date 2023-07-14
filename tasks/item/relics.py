from module.base.timer import Timer
from module.logger import logger
from tasks.base.assets.assets_base_page import CLOSE
from tasks.base.assets.assets_base_popup import CONFIRM_POPUP
from tasks.item.assets.assets_item_relics import *
from tasks.item.keywords import KEYWORD_ITEM_TAB
from tasks.item.ui import ItemUI


class RelicsUI(ItemUI):
    def salvage_relic(self, skip_first_screenshot=True) -> bool:
        logger.hr('Salvage Relic', level=2)
        self.item_goto(KEYWORD_ITEM_TAB.Relics, wait_until_stable=False)
        interval = Timer(1)
        while 1:  # relic tab -> salvage
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(REVERSE_ORDER):
                break
            if self.appear_then_click(GOTO_SALVAGE):
                continue

        skip_first_screenshot = True
        while 1:  # salvage -> first relic selected
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(REVERSE_ORDER):  # this should judge before break condition
                continue
            if self.appear(SALVAGE):
                break
            if interval.reached() and self.image_color_count(FIRST_RELIC, (233, 192, 108)):
                self.device.click(FIRST_RELIC)
                interval.reset()
                continue

        skip_first_screenshot = True
        while 1:  # selected -> rewards claimed
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.handle_reward():
                logger.info("Relic salvaged")
                break
            if self.appear_then_click(SALVAGE):
                continue
            if self.appear_then_click(CONFIRM_POPUP):
                continue

        skip_first_screenshot = True
        while 1:  # rewards claimed -> relic tab page
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(GOTO_SALVAGE):
                logger.info("Salvage page exited")
                break
            if self.appear_then_click(CLOSE, interval=1):
                continue
        return True
