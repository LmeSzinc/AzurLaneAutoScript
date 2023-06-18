from module.ocr.ocr import *
from module.ui.scroll import Scroll
from tasks.base.assets.assets_base_page import MENU_CHECK, SYNTHESIZE_CHECK
from tasks.base.assets.assets_base_popup import GET_REWARD
from tasks.base.page import Page, page_menu, page_synthesize
from tasks.base.ui import UI
from tasks.daily.assets.assets_daily_synthesize_consumable import *


class SynthesizeUI(UI):
    def ensure_scroll_top(self, page: str | Page, skip_first_screenshot=False) -> None:
        """
        Args:
            page:
            skip_first_screenshot:

        Examples:
            self = SynthesizeUI('alas')
            self.device.screenshot()
            self.ensure_scroll_top(page=page_menu)
        """
        if isinstance(page, Page):
            page = page.name

        match page:
            case page_menu.name:
                check_image = MENU_CHECK
                scroll = Scroll((1177, 261, 1183, 682), color=(191, 191, 191), name='MENU_SCROLL')
            case page_synthesize.name:
                check_image = SYNTHESIZE_CHECK
                scroll = Scroll((458, 80, 463, 662), color=(210, 210, 210), name='SYNTHESIZE_SCROLL')
            case _:
                logger.info(f'No page matched, just skip')
                return

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if not self.appear(check_image):
                logger.info(f'Current page is not {page} page, just skip')
                break
            if not scroll.appear(main=self):
                logger.info(f'{page} scroll can not find, just skip')
                break

            # Determine whether the scroll bar at the top,
            # and if it does not, pull the scroll bar to the top
            if scroll.at_top(main=self):
                logger.info(f'{page} scroll at the top')
                break
            if not scroll.at_top(main=self):
                logger.info(f'Pull the {page} scroll bar to the top')
                scroll.set_top(main=self)
                continue


class SynthesizeConsumablesUI(SynthesizeUI):
    def synthesize_consumables(self) -> bool:
        """
        Returns:
            bool:

        Examples:
            self = SynthesizeConsumablesUI('alas')
            self.device.screenshot()
            result = self.synthesize_consumables()
        """
        logger.hr('Synthesize consumables', level=2)
        # If the current page is not the menu page,
        # the menu scroll bar must be at the top when opening the menu page from other page,
        # so first step is determine whether the scroll bar is at the top
        self.ensure_scroll_top(page=page_menu)

        self.ui_ensure(page_synthesize)
        self._switch_tag_to_consumables()
        self.ensure_scroll_top(page=page_synthesize)
        if self._select_items():
            self._open_synthesize_popup()
            self._synthesize_confirm()
            self._back_to_synthesize_page()
            return True
        else:
            return False

    def _switch_tag_to_consumables(self, skip_first_screenshot=True):
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(SYNTHESIZE_CONSUMABLES_CHECK):
                logger.info('Synthesize consumables page appear')
                break
            # Switch to consumables subpage
            if self.appear_then_click(SYNTHESIZE_GOTO_CONSUMABLES):
                logger.info('Switch to consumables subpage')
                continue

    def _select_items(self) -> bool:
        candidate_items = {
            CONSUMABLES_TRICK_SNACK: CONSUMABLES_TRICK_SNACK_CHECK,
            CONSUMABLES_COMFORT_FOOD: CONSUMABLES_COMFORT_FOOD_CHECK,
            CONSUMABLES_SIMPLE_AED: CONSUMABLES_SIMPLE_AED_CHECK
        }
        for item, item_check in candidate_items.items():
            # Determine if the "item" can be found and synthesized in the left item column
            if item.match_template_color(self.device.image):
                logger.info('Find an item that can be synthesized')
                # Ensure that item is selected
                skip_first_screenshot = True
                while 1:
                    if skip_first_screenshot:
                        skip_first_screenshot = False
                    else:
                        self.device.screenshot()
                    if self.appear(item_check):
                        logger.info('Consumables that can be synthesized have been selected')
                        return True
                    if self.appear_then_click(item):
                        continue
        else:
            logger.info('There are no suitable items to synthesize')
            return False

    def _open_synthesize_popup(self, skip_first_screenshot=True):
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(SYNTHESIZE_CONFIRM_POPUP):
                logger.info('Synthesize confirm popup window appear')
                break
            # The recipe of the item has not been unlocked yet, but it can be unlocked now
            # Click the "recipe unlock" button to unlock the synthesize recipe
            if self.appear_then_click(RECIPE_UNLOCK):
                logger.info('Unlock the synthesize recipe')
                continue
            # click the "synthesize" button to open the synthesize popup window
            if self.appear_then_click(SYNTHESIZE_CONFIRM):
                logger.info('Click the synthesize button')
                continue

    def _synthesize_confirm(self, skip_first_screenshot=True):
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(GET_REWARD):
                logger.info('Synthesize consumable completed')
                break
            # Synthesize confirm
            if self.appear_then_click(SYNTHESIZE_CONFIRM_POPUP):
                logger.info('Click the confirm button')
                continue

    def _back_to_synthesize_page(self, skip_first_screenshot=True):
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(SYNTHESIZE_CONSUMABLES_CHECK):
                logger.info('Synthesize consumables page appear')
                break
            # Go back to the previous page
            if self.appear_then_click(GET_REWARD):
                logger.info('Click on the blank space to back to the synthesize consumables page')
                continue
