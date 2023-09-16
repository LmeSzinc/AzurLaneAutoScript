from module.ocr.ocr import *
from module.ui.scroll import Scroll
from tasks.base.assets.assets_base_popup import POPUP_CONFIRM
from tasks.base.page import page_item
from tasks.daily.assets.assets_daily_synthesize_consumable import \
    SIMPLE_PROTECTIVE_GEAR as SYNTHESIZE_SIMPLE_PROTECTIVE_GEAR, \
    SIMPLE_PROTECTIVE_GEAR_CHECK as SYNTHESIZE_SIMPLE_PROTECTIVE_GEAR_CHECK
from tasks.daily.synthesize import SynthesizeConsumablesUI
from tasks.item.assets.assets_item_consumable_usage import *
from tasks.item.assets.assets_item_ui import CONSUMABLE_CHECK
from tasks.item.keywords import KEYWORD_ITEM_TAB
from tasks.item.ui import ItemUI


class ConsumableUsageUI(ItemUI):
    def use_consumable(self, synthesize_or_not: bool = True) -> bool:
        """
        Args:
            synthesize_or_not(bool):

        Returns:
            bool: If success

        Examples:
            self = ConsumableUsageUI('alas')
            self.device.screenshot()
            result = self.use_consumable()
        """
        logger.hr('Use consumable', level=2)
        self.ui_ensure(page_item)
        self.item_goto(KEYWORD_ITEM_TAB.Consumables)
        if self._search_and_select_consumable():
            self._click_use()
            self._confirm_use()
            return True
        else:
            # Prevent matching errors from causing continuous synthesis of consumables
            if not synthesize_or_not:
                return False
            if SynthesizeConsumablesUI(self.config, self.device).synthesize_consumables(
                    SYNTHESIZE_SIMPLE_PROTECTIVE_GEAR, SYNTHESIZE_SIMPLE_PROTECTIVE_GEAR_CHECK
            ):
                return self.use_consumable(synthesize_or_not=False)
            else:
                return False

    def _search_and_select_consumable(self, skip_first_screenshot=True) -> bool:
        logger.info('Search consumable')
        # If the default subpage is the consumables page, it is necessary to screenshot and check subpage again,
        # because in this scenario, scroll bar delay appears and the previous screenshot was
        # taken after clicking on the "item" to determine whether to enter the "item", which may be inaccurate
        # self._switch_tag_to_consumables(False)
        self.item_goto(KEYWORD_ITEM_TAB.Consumables)

        # Determine if there is a scroll bar. If there is a scroll bar,
        # pull it down and check if the consumable to be used can be found
        scroll = Scroll(area=ITEM_CONSUMABLE_SCROLL.button, color=(200, 200, 200), name=ITEM_CONSUMABLE_SCROLL.name)
        if scroll.appear(main=self):
            if not scroll.at_top(main=self):
                scroll.set_top(main=self)
            while 1:
                if skip_first_screenshot:
                    skip_first_screenshot = False
                else:
                    self.device.screenshot()

                # Determine if the specified consumable can be found
                if self.appear(SIMPLE_PROTECTIVE_GEAR_CHECK):
                    logger.info('The consumable to be used have been selected')
                    return True
                if scroll.at_bottom(main=self) and not self.appear(SIMPLE_PROTECTIVE_GEAR, similarity=0.7):
                    logger.info('Can not find the consumable which to be used, just skip')
                    return False
                if self.appear_then_click(SIMPLE_PROTECTIVE_GEAR, similarity=0.7, interval=2):
                    logger.info('Select the consumable which to be used')
                    continue
                # Scroll bar flipping
                if not scroll.at_bottom(main=self):
                    scroll.next_page(main=self)
                    continue
        else:
            # Determine if the specified consumable can be found
            if self.appear(SIMPLE_PROTECTIVE_GEAR, similarity=0.7):
                while 1:
                    if skip_first_screenshot:
                        skip_first_screenshot = False
                    else:
                        self.device.screenshot()

                    if self.appear(SIMPLE_PROTECTIVE_GEAR_CHECK):
                        logger.info('The consumable to be used have been selected')
                        return True
                    if self.appear_then_click(SIMPLE_PROTECTIVE_GEAR, similarity=0.7, interval=2):
                        logger.info('Select the consumable which to be used')
                        continue
            else:
                logger.info('Can not find the consumable which to be used, just skip')
                return False

    def _click_use(self, skip_first_screenshot=True):
        """
        Description:
            Because after executing "using consumable",
            there will be a brief animation that will directly return to the consumables page,
            so "click to use" and "confirm to use" have been split into two steps
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(POPUP_CONFIRM):
                logger.info('Item consumable usage popup appear')
                break
            if self.appear_then_click(USE_CONSUMABLE, interval=2):
                logger.info('Click the "use" button')
                continue

    def _confirm_use(self, skip_first_screenshot=True):
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(CONSUMABLE_CHECK):
                logger.info('Complete using consumables')
                break
            # If there is already consumable effect, a confirmation box will pop up again,
            # so shorten the judgment interval of the confirmation box
            if self.handle_popup_confirm(interval=1):
                logger.info('Confirm the use of consumable')
                continue
