from module.ocr.ocr import *
from module.ui.scroll import Scroll
from tasks.base.assets.assets_base_page import MENU_CHECK, SYNTHESIZE_CHECK
from tasks.base.assets.assets_base_popup import GET_REWARD
from tasks.base.page import Page, page_menu, page_synthesize
from tasks.base.ui import UI
from tasks.base.assets.assets_base_page import MENU_SCROLL
from tasks.base.assets.assets_base_popup import CONFIRM_POPUP
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
                scroll = Scroll(MENU_SCROLL.button, color=(191, 191, 191), name=MENU_SCROLL.name)
            case page_synthesize.name:
                check_image = SYNTHESIZE_CHECK
                scroll = Scroll(SYNTHESIZE_SCROLL.button, color=(210, 210, 210), name=SYNTHESIZE_SCROLL.name)
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
    def synthesize_consumables(self, target_button: ButtonWrapper = None,
                               target_button_check: ButtonWrapper = None) -> bool:
        """
        Args:
            target_button(ButtonWrapper):
            target_button_check(ButtonWrapper):

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
        if self._search_and_select_items(target_button, target_button_check):
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

    def _select_items(self, candidate_items: dict[ButtonWrapper, ButtonWrapper]) -> bool:
        for item, item_check in candidate_items.items():
            # Determine if the "item" can be found and synthesized in the left item column
            if item.match_template_color(self.device.image, similarity=0.7):
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
                    if self.appear_then_click(item, similarity=0.7):
                        continue
        else:
            return False

    def _search_and_select_items(self, target_button: ButtonWrapper = None,
                                 target_button_check: ButtonWrapper = None) -> bool:
        candidate_items = {target_button: target_button_check} if target_button and target_button_check else {
            CONSUMABLES_TRICK_SNACK: CONSUMABLES_TRICK_SNACK_CHECK,
            CONSUMABLES_COMFORT_FOOD: CONSUMABLES_COMFORT_FOOD_CHECK,
            CONSUMABLES_SIMPLE_AED: CONSUMABLES_SIMPLE_AED_CHECK
        }

        # Search target button from top to bottom
        scroll = Scroll(SYNTHESIZE_SCROLL.button, color=(210, 210, 210), name=SYNTHESIZE_SCROLL.name)
        if scroll.appear(main=self):
            skip_first_screenshot = True
            while 1:
                if skip_first_screenshot:
                    skip_first_screenshot = False
                else:
                    self.device.screenshot()
                if self._select_items(candidate_items):
                    return True
                if scroll.at_bottom(main=self):
                    logger.info('There are no suitable items to synthesize')
                    return False
                if not scroll.at_bottom(main=self):
                    scroll.next_page(main=self)
                    continue
        else:
            return self._select_items(candidate_items)

    def _open_synthesize_popup(self, skip_first_screenshot=True):
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(CONFIRM_POPUP):
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
            if self.appear_then_click(CONFIRM_POPUP):
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
