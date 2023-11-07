from module.ocr.ocr import *
from module.ui.scroll import Scroll
from tasks.base.assets.assets_base_page import MENU_CHECK, MENU_SCROLL, SYNTHESIZE_CHECK
from tasks.base.assets.assets_base_popup import POPUP_CONFIRM
from tasks.base.page import Page, page_menu, page_synthesize
from tasks.base.ui import UI
from tasks.daily.assets.assets_daily_synthesize_consumable import *
from tasks.daily.assets.assets_daily_synthesize_material import *


class SynthesizeUI(UI):
    # Default list of candidate items
    default_candidate_items = {}

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

    def _ensure_synthesize_page(self):
        # If the current page is not the menu page,
        # the menu scroll bar must be at the top when opening the menu page from other page,
        # so first step is determine whether the scroll bar is at the top
        self.ensure_scroll_top(page=page_menu)
        self.ui_ensure(page_synthesize)

    # Default subpage is consumables
    def _switch_subpage(self, skip_first_screenshot=True, subpage: ButtonWrapper = SYNTHESIZE_GOTO_CONSUMABLES,
                        subpage_check: ButtonWrapper = SYNTHESIZE_CONSUMABLES_CHECK):
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(subpage_check):
                logger.info(f'Synthesize {subpage.name} subpage appear')
                break
            # Switch to subpage
            if self.appear_then_click(subpage):
                logger.info(f'Switch to {subpage.name} subpage')
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
                        logger.info('Item that can be synthesized has been selected')
                        return True
                    if self.appear_then_click(item, similarity=0.7):
                        continue
        else:
            return False

    def _search_and_select_items(self, target_button: ButtonWrapper = None,
                                 target_button_check: ButtonWrapper = None) -> bool:
        candidate_items = {target_button: target_button_check} if target_button and target_button_check \
            else self.__class__.default_candidate_items

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

            if self.appear(POPUP_CONFIRM):
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

            if self.reward_appear():
                logger.info('Synthesize consumable completed')
                break
            # Synthesize confirm
            if self.handle_popup_confirm():
                continue

    def _back_to_synthesize_page(self, skip_first_screenshot=True):
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(SYNTHESIZE_CHECK):
                logger.info('Synthesize consumables page appear')
                break
            # Go back to the previous page
            if self.handle_reward(interval=2):
                logger.info('Click on the blank space to back to synthesize page')
                continue

    def _synthesize(self, target_button: ButtonWrapper = None,
                    target_button_check: ButtonWrapper = None) -> bool:
        self.ensure_scroll_top(page=page_synthesize)
        if self._search_and_select_items(target_button, target_button_check):
            self._open_synthesize_popup()
            self._synthesize_confirm()
            self._back_to_synthesize_page()
            return True
        else:
            return False


class SynthesizeConsumablesUI(SynthesizeUI):
    # Selected three items that are easiest to obtain their synthetic materials
    default_candidate_items = {
        CONSUMABLES_TRICK_SNACK: CONSUMABLES_TRICK_SNACK_CHECK,
        CONSUMABLES_COMFORT_FOOD: CONSUMABLES_COMFORT_FOOD_CHECK,
        CONSUMABLES_SIMPLE_AED: CONSUMABLES_SIMPLE_AED_CHECK
    }

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
        self._ensure_synthesize_page()
        self._switch_subpage(subpage=SYNTHESIZE_GOTO_CONSUMABLES, subpage_check=SYNTHESIZE_CONSUMABLES_CHECK)
        return self._synthesize(target_button, target_button_check)


class SynthesizeMaterialUI(SynthesizeUI):
    # Selected three items that are easiest to obtain their synthetic materials
    default_candidate_items = {
        GLIMMERING_CORE: GLIMMERING_CORE_CHECK,
        USURPERS_SCHEME: USURPERS_SCHEME_CHECK,
        SILVERMANE_INSIGNIA: SILVERMANE_INSIGNIA_CHECK
    }

    def synthesize_material(self, target_button: ButtonWrapper = None,
                            target_button_check: ButtonWrapper = None) -> bool:
        """
        Args:
            target_button(ButtonWrapper):
            target_button_check(ButtonWrapper):

        Returns:
            bool:

        Examples:
            self = SynthesizeMaterialUI('alas')
            self.device.screenshot()
            result = self.synthesize_material()
        """

        logger.hr('Synthesize material', level=2)
        self._ensure_synthesize_page()
        self._switch_subpage(subpage=SYNTHESIZE_GOTO_MATERIAL, subpage_check=SYNTHESIZE_MATERIAL_CHECK)
        return self._synthesize(target_button, target_button_check)
