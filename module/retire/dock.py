import module.config.server as server

from module.base.button import ButtonGrid, get_color, color_similar
from module.base.decorator import cached_property
from module.base.timer import Timer
from module.equipment.equipment import Equipment
from module.logger import logger
from module.ocr.ocr import DigitCounter
from module.retire.assets import *
from module.ui.scroll import Scroll
from module.ui.setting import Setting
from module.ui.switch import Switch

DOCK_SORTING = Switch('Dork_sorting')
DOCK_SORTING.add_state('Ascending', check_button=SORT_ASC, click_button=SORTING_CLICK)
DOCK_SORTING.add_state('Descending', check_button=SORT_DESC, click_button=SORTING_CLICK)

DOCK_FAVOURITE = Switch('Favourite_filter')
DOCK_FAVOURITE.add_state('on', check_button=COMMON_SHIP_FILTER_ENABLE)
DOCK_FAVOURITE.add_state('off', check_button=COMMON_SHIP_FILTER_DISABLE)

CARD_GRIDS = ButtonGrid(
    origin=(93, 76), delta=(164 + 2 / 3, 227), button_shape=(138, 204), grid_shape=(7, 2), name='CARD')
CARD_RARITY_GRIDS = CARD_GRIDS.crop(area=(0, 0, 138, 5), name='RARITY')
if server.server != 'jp':
    CARD_LEVEL_GRIDS = CARD_GRIDS.crop(area=(77, 5, 138, 27), name='LEVEL')
    CARD_EMOTION_GRIDS = CARD_GRIDS.crop(area=(23, 29, 48, 52), name='EMOTION')
else:
    CARD_LEVEL_GRIDS = CARD_GRIDS.crop(area=(74, 5, 136, 27), name='LEVEL')
    CARD_EMOTION_GRIDS = CARD_GRIDS.crop(area=(21, 29, 71, 48), name='EMOTION')

DOCK_SCROLL = Scroll(DOCK_SCROLL, color=(247, 211, 66), name='DOCK_SCROLL')

OCR_DOCK_SELECTED = DigitCounter(DOCK_SELECTED, threshold=64, name='OCR_DOCK_SELECTED')


class Dock(Equipment):
    def handle_dock_cards_loading(self, skip_first_screenshot=True):
        # Poor implementation
        # confirm_timer method cannot be used
        timeout = Timer(1.2, count=1).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # Quick exit if dock is empty
            if self.appear(DOCK_EMPTY):
                logger.info('Dock empty')
                break
            # Otherwise we just wait 1.2s
            if timeout.reached():
                break

    def dock_favourite_set(self, enable=False, wait_loading=True):
        """
        Args:
            enable: True to filter favourite ships only
            wait_loading: Default to True, use False on continuous operation
        """
        if DOCK_FAVOURITE.set('on' if enable else 'off', main=self):
            if wait_loading:
                self.handle_dock_cards_loading()

    def _dock_quit_check_func(self):
        return not self.appear(DOCK_CHECK, offset=(20, 20))

    def dock_quit(self):
        self.ui_back(check_button=self._dock_quit_check_func, skip_first_screenshot=True)

    def dock_sort_method_dsc_set(self, enable=True, wait_loading=True):
        """
        Args:
            enable: True to set descending sorting
            wait_loading: Default to True, use False on continuous operation
        """
        if DOCK_SORTING.set('Descending' if enable else 'Ascending', main=self):
            if wait_loading:
                self.handle_dock_cards_loading()

    def dock_filter_enter(self):
        self.ui_click(DOCK_FILTER, appear_button=DOCK_CHECK, check_button=DOCK_FILTER_CONFIRM,
                      skip_first_screenshot=True)

    def dock_filter_confirm(self, wait_loading=True):
        """
        Args:
            wait_loading: Default to True, use False on continuous operation
        """
        self.ui_click(DOCK_FILTER_CONFIRM, check_button=DOCK_CHECK, skip_first_screenshot=True)
        if wait_loading:
            self.handle_dock_cards_loading()

    @cached_property
    def dock_filter(self) -> Setting:
        delta = (147 + 1 / 3, 57)
        button_shape = (139, 42)
        setting = Setting(name='DOCK', main=self)
        setting.add_setting(
            setting='sort',
            option_buttons=ButtonGrid(
                origin=(218, 65), delta=delta, button_shape=button_shape, grid_shape=(7, 1), name='FILTER_SORT'),
            # stat has extra grid, not worth pursuing
            option_names=['rarity', 'level', 'total', 'join', 'intimacy', 'mood', 'stat'],
            option_default='level'
        )
        setting.add_setting(
            setting='index',
            option_buttons=ButtonGrid(
                origin=(218, 138), delta=delta, button_shape=button_shape, grid_shape=(7, 2), name='FILTER_INDEX'),
            option_names=['all', 'vanguard', 'main', 'dd', 'cl', 'ca', 'bb',
                          'cv', 'repair', 'ss', 'others', 'not_available', 'not_available', 'not_available'],
            option_default='all'
        )
        setting.add_setting(
            setting='faction',
            option_buttons=ButtonGrid(
                origin=(218, 268), delta=delta, button_shape=button_shape, grid_shape=(7, 2), name='FILTER_FACTION'),
            option_names=['all', 'eagle', 'royal', 'sakura', 'iron', 'dragon', 'sardegna',
                          'northern', 'iris', 'vichya', 'other', 'not_available', 'not_available', 'not_available'],
            option_default='all'
        )
        setting.add_setting(
            setting='rarity',
            option_buttons=ButtonGrid(
                origin=(218, 398), delta=delta, button_shape=button_shape, grid_shape=(7, 1), name='FILTER_RARITY'),
            option_names=['all', 'common', 'rare', 'elite', 'super_rare', 'ultra', 'not_available'],
            option_default='all'
        )
        setting.add_setting(
            setting='extra',
            option_buttons=ButtonGrid(
                origin=(218, 471), delta=delta, button_shape=button_shape, grid_shape=(7, 2), name='FILTER_EXTRA'),
            option_names=['no_limit', 'has_skin', 'can_retrofit', 'enhanceable', 'can_limit_break', 'not_level_max', 'can_awaken',
                          'can_awaken_plus', 'special', 'oath_skin', 'unique_augment_module', 'not_available', 'not_available', 'not_available'],
            option_default='no_limit'
        )
        return setting

    def dock_filter_set(
            self,
            sort='level',
            index='all',
            faction='all',
            rarity='all',
            extra='no_limit',
            wait_loading=True
    ):
        """
        A faster filter set function.

        Args:
            sort (str, list):
                ['rarity', 'level', 'total', 'join', 'intimacy', 'mood', 'stat']
            index (str, list):
                ['all', 'vanguard', 'main', 'dd', 'cl', 'ca', 'bb',
                 'cv', 'repair', 'ss', 'others', 'not_available', 'not_available', 'not_available']
            faction (str, list):
                ['all', 'eagle', 'royal', 'sakura', 'iron', 'dragon', 'sardegna',
                 'northern', 'iris', 'vichya', 'other', 'not_available', 'not_available', 'not_available']
            rarity (str, list):
                ['all', 'common', 'rare', 'elite', 'super_rare', 'ultra', 'not_available']
            extra (str, list):
                ['no_limit', 'has_skin', 'can_retrofit', 'enhanceable', 'can_limit_break', 'not_level_max', 'can_awaken',
                 'can_awaken_plus', 'special', 'oath_skin', 'unique_augment_module', 'not_available', 'not_available', 'not_available'],

        Pages:
            in: page_dock
        """
        self.dock_filter_enter()
        self.dock_filter.set(sort=sort, index=index, faction=faction, rarity=rarity, extra=extra)
        self.dock_filter_confirm(wait_loading=wait_loading)

    def dock_select_one(self, button, skip_first_screenshot=True):
        """
        Args:
            button (Button): Ship button to select
            skip_first_screenshot:
        """
        # if self.config.SERVER == 'en':
        #     logger.info('EN has no dock_selected check currently, use plain click')
        #
        #     self.device.click(button)
        #
        #     while 1:
        #         self.device.screenshot()
        #
        #         if self.appear(DOCK_CHECK, offset=(20, 20)):
        #             break
        #         if self.handle_popup_confirm('DOCK_SELECT'):
        #             continue
        #     return

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.dock_selected():
                break

            if self.appear(DOCK_CHECK, offset=(20, 20), interval=5):
                self.device.click(button)
                continue
            if self.handle_popup_confirm('DOCK_SELECT'):
                continue

    def dock_selected(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot:

        Returns:
            bool: If selected a ship in dock.
                True for ship counter 1/1, False for 0/1.
        """
        # if self.config.SERVER == 'en':
        #     logger.info('EN has no dock_selected check currently, assume not selected')
        #     return False

        current = 0
        timeout = Timer(1.5, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Get dock_selected timeout, assume not selected')
                break

            current, _, total = OCR_DOCK_SELECTED.ocr(self.device.image)
            if total == 1:
                break

        return current > 0

    def dock_select_confirm(self, check_button, skip_first_screenshot=True):
        """
        Args:
            check_button (callable, Button):
            skip_first_screenshot:
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.ui_process_check_button(check_button):
                break

            if self.appear_then_click(SHIP_CONFIRM, offset=(200, 50), interval=5):
                continue
            if self.handle_popup_confirm('DOCK_SELECT_CONFIRM'):
                continue

    def dock_enter_first(self, non_npc=True, skip_first_screenshot=True):
        """
        Enter first ship in dock

        Args:
            non_npc: True to enter the second ship if first ship is NPC
            skip_first_screenshot:

        Returns:
            bool: True if success to enter
                False if dock empty
                False if non_npc and only one NPC in dock

        Pages:
            in: page_dock
            out: SHIP_DETAIL_CHECK
        """
        logger.info('Dock enter first')
        self.interval_clear(DOCK_CHECK, interval=3)

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(SHIP_DETAIL_CHECK, offset=(20, 20)):
                return True
            if self.appear(DOCK_EMPTY, offset=(20, 20)):
                logger.info('Dock empty')
                return False

            # Click
            if self.appear(DOCK_CHECK, offset=(20, 20), interval=3):
                if non_npc:
                    # Check NPC
                    if DOCK_FIRST_NPC.match_luma(self.device.image, offset=(20, 20)):
                        logger.info('First ship is NPC, select second')
                        button = CARD_GRIDS[(1, 0)]
                        # Check if there's second ship
                        color = get_color(self.device.image, button.area)
                        if color_similar(color, (34, 34, 42)):
                            logger.info('Second ship empty, dock empty')
                            return False
                    else:
                        button = CARD_GRIDS[(0, 0)]
                else:
                    button = CARD_GRIDS[(0, 0)]
                self.device.click(button)
                continue
            if self.handle_game_tips():
                continue
