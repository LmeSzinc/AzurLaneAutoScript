import numpy as np

from module.base.base import ModuleBase
from module.base.button import ClickButton
from module.base.timer import Timer
from module.base.utils import get_color
from module.logger import logger
from module.ocr.ocr import Ocr, OcrResultButton
from module.ocr.utils import split_and_pair_button_attr
from module.ui.draggable_list import DraggableList
from module.ui.switch import Switch
from tasks.base.assets.assets_base_page import FORGOTTEN_HALL_CHECK
from tasks.base.page import page_guide
from tasks.base.ui import UI
from tasks.combat.assets.assets_combat_prepare import COMBAT_PREPARE
from tasks.dungeon.assets.assets_dungeon_ui import *
from tasks.dungeon.keywords import (
    DungeonList,
    DungeonNav,
    DungeonTab,
    KEYWORDS_DUNGEON_ENTRANCE,
    KEYWORDS_DUNGEON_NAV,
    KEYWORDS_DUNGEON_TAB
)
from tasks.dungeon.keywords.classes import DungeonEntrance


class DungeonTabSwitch(Switch):
    def click(self, state, main):
        """
        Args:
            state (str):
            main (ModuleBase):
        """
        button = self.get_data(state)['click_button']
        _ = main.appear(button)  # Search button to load offset
        main.device.click(button)


SWITCH_DUNGEON_TAB = DungeonTabSwitch('DungeonTab', is_selector=True)
SWITCH_DUNGEON_TAB.add_state(
    KEYWORDS_DUNGEON_TAB.Operation_Briefing,
    check_button=OPERATION_BRIEFING_CHECK,
    click_button=OPERATION_BRIEFING_CLICK
)
SWITCH_DUNGEON_TAB.add_state(
    KEYWORDS_DUNGEON_TAB.Daily_Training,
    check_button=DAILY_TRAINING_CHECK,
    click_button=DAILY_TRAINING_CLICK
)
SWITCH_DUNGEON_TAB.add_state(
    KEYWORDS_DUNGEON_TAB.Survival_Index,
    check_button=SURVIVAL_INDEX_CHECK,
    click_button=SURVIVAL_INDEX_CLICK
)


class OcrDungeonNav(Ocr):
    def after_process(self, result):
        result = super().after_process(result)
        result = result.replace('#', '')
        if self.lang == 'ch':
            result = result.replace('萼喜', '萼')
            result = result.replace('带', '滞')  # 凝带虚影
        return result


class OcrDungeonList(Ocr):
    def after_process(self, result):
        result = super().after_process(result)
        if self.lang == 'ch':
            result = result.replace('翼', '巽')  # 巽风之形
            result = result.replace('皖A0', '50').replace('皖', '')
        return result


class OcrDungeonListLimitEntrance(OcrDungeonList):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.button = ClickButton((*self.button.area[:3], self.button.area[3] - 70))


class DraggableDungeonNav(DraggableList):
    # 0.5 is the magic number to reach bottom in 1 swipe
    # but relax we still have retires when magic doesn't work
    drag_vector = (0.50, 0.52)


class DraggableDungeonList(DraggableList):
    teleports: list[OcrResultButton] = []
    navigates: list[OcrResultButton] = []

    def load_rows(self, main: ModuleBase):
        super().load_rows(main=main)
        # Replace dungeon.button with teleport
        self.teleports = list(split_and_pair_button_attr(
            DUNGEON_LIST.cur_buttons,
            split_func=lambda x: x != KEYWORDS_DUNGEON_ENTRANCE.Teleport,
            relative_area=(0, 0, 1280, 120)
        ))
        self.navigates = list(split_and_pair_button_attr(
            DUNGEON_LIST.cur_buttons,
            split_func=lambda x: x != KEYWORDS_DUNGEON_ENTRANCE.Navigate,
            relative_area=(0, 0, 1280, 120)
        ))


DUNGEON_NAV_LIST = DraggableDungeonNav(
    'DungeonNavList', keyword_class=DungeonNav, ocr_class=OcrDungeonNav, search_button=OCR_DUNGEON_NAV)
DUNGEON_LIST = DraggableDungeonList(
    'DungeonList', keyword_class=[DungeonList, DungeonEntrance],
    ocr_class=OcrDungeonList, search_button=OCR_DUNGEON_LIST)


class DungeonUI(UI):
    def dungeon_tab_goto(self, state: DungeonTab):
        """
        Args:
            state:

        Returns:
            bool: If UI switched

        Examples:
            self = DungeonUI('alas')
            self.device.screenshot()
            self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Operation_Briefing)
            self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Daily_Training)
            self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Survival_Index)
        """
        logger.hr('Dungeon tab goto', level=2)
        ui_switched = self.ui_ensure(page_guide)
        tab_switched = SWITCH_DUNGEON_TAB.set(state, main=self)

        if ui_switched or tab_switched:
            if state == KEYWORDS_DUNGEON_TAB.Daily_Training:
                logger.info(f'Tab goto {state}, wait until loaded')
                self._dungeon_wait_daily_training_loaded()
            elif state == KEYWORDS_DUNGEON_TAB.Survival_Index:
                logger.info(f'Tab goto {state}, wait until loaded')
                self._dungeon_wait_survival_loaded()
            return True
        else:
            return False

    def _dungeon_wait_daily_training_loaded(self, skip_first_screenshot=True):
        """
        Returns:
            bool: True if wait success, False if wait timeout.

        Pages:
            in: page_guide, Daily_Training
        """
        timeout = Timer(2, count=4).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Wait daily training loaded timeout')
                return False
            color = get_color(self.device.image, DAILY_TRAINING_LOADED.area)
            if np.mean(color) < 128:
                logger.info('Daily training loaded')
                return True

    def _dungeon_wait_survival_loaded(self, skip_first_screenshot=True):
        """
        Returns:
            bool: True if wait success, False if wait timeout.

        Pages:
            in: page_guide, Survival_Index
        """
        timeout = Timer(2, count=4).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Wait survival index loaded timeout')
                return False
            if self.appear(SURVIVAL_INDEX_LOADED):
                logger.info('Survival index loaded')
                return True

    def _dungeon_wait_until_forgotten_hall_stabled(self, skip_first_screenshot=True):
        """
        Returns:
            bool: True if wait success, False if wait timeout.

        Pages:
            in: page_guide, Survival_Index
        """
        # Wait until Forgotten_Hall stabled
        timeout = Timer(2, count=4).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if timeout.reached():
                logger.warning('Wait until Forgotten_Hall stabled timeout')
                return False

            DUNGEON_NAV_LIST.load_rows(main=self)

            # End
            button = DUNGEON_NAV_LIST.keyword2button(KEYWORDS_DUNGEON_NAV.Forgotten_Hall)
            if button:
                # 513 is the top of the last row of DungeonNav
                if button.area[1] > 513:
                    logger.info('DungeonNav row Forgotten_Hall stabled')
                    return True

    def _dungeon_nav_goto(self, dungeon: DungeonList, skip_first_screenshot=True):
        """
        Equivalent to `DUNGEON_NAV_LIST.select_row(dungeon.dungeon_nav, main=self)`
        but with tricks to be faster

        Args:
            dungeon:
            skip_first_screenshot:
        """
        logger.hr('Dungeon nav goto', level=2)
        logger.info(f'Dungeon nav goto {dungeon.dungeon_nav}')

        # Wait rows
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            DUNGEON_NAV_LIST.load_rows(main=self)
            if DUNGEON_NAV_LIST.cur_buttons:
                break

        # Check if it's at the first page.
        if DUNGEON_NAV_LIST.keyword2button(KEYWORDS_DUNGEON_NAV.Simulated_Universe, show_warning=False):
            # Going to use a faster method to navigate but can only start from list top
            logger.info('DUNGEON_NAV_LIST at top')
        else:
            # To start from any list states.
            logger.info('DUNGEON_NAV_LIST not at top')
            DUNGEON_NAV_LIST.select_row(dungeon.dungeon_nav, main=self)
            return True

        # Check the first page
        if dungeon.dungeon_nav in [
            KEYWORDS_DUNGEON_NAV.Simulated_Universe,
            KEYWORDS_DUNGEON_NAV.Calyx_Golden,
            KEYWORDS_DUNGEON_NAV.Calyx_Crimson,
            KEYWORDS_DUNGEON_NAV.Stagnant_Shadow,
            KEYWORDS_DUNGEON_NAV.Cavern_of_Corrosion,
        ]:
            button = DUNGEON_NAV_LIST.keyword2button(dungeon.dungeon_nav)
            if button:
                DUNGEON_NAV_LIST.select_row(dungeon.dungeon_nav, main=self, insight=False)
                return True

        # Check the second page
        while 1:
            DUNGEON_NAV_LIST.drag_page('down', main=self)
            # No skip_first_screenshot since drag_page is just called
            if self._dungeon_wait_until_forgotten_hall_stabled(skip_first_screenshot=False):
                DUNGEON_NAV_LIST.select_row(dungeon.dungeon_nav, main=self, insight=False)
                return True

    def _dungeon_insight(self, dungeon: DungeonList):
        """
        Pages:
            in: page_guide, Survival_Index, nav including dungeon
            out: page_guide, Survival_Index, nav including dungeon, dungeon insight
        """
        logger.hr('Dungeon insight', level=2)
        # Insight dungeon
        DUNGEON_LIST.insight_row(dungeon, main=self)
        # Check if dungeon unlocked
        for entrance in DUNGEON_LIST.navigates:
            entrance: OcrResultButton = entrance
            logger.warning(f'Teleport {entrance.matched_keyword} is not unlocked')
            if entrance == dungeon:
                logger.error(f'Trying to enter dungeon {dungeon}, but teleport is not unlocked')
                return False

        # Find teleport button
        if dungeon not in [tp.matched_keyword for tp in DUNGEON_LIST.teleports]:
            # Dungeon name is insight but teleport button is not
            logger.info('Dungeon name is insight, swipe down a little bit to find the teleport button')
            if dungeon.is_Forgotten_Hall:
                DUNGEON_LIST.drag_vector = (-0.4, -0.2)  # Keyword loaded is reversed
            else:
                DUNGEON_LIST.drag_vector = (0.2, 0.4)
            DUNGEON_LIST.ocr_class = OcrDungeonListLimitEntrance
            DUNGEON_LIST.insight_row(dungeon, main=self)
            DUNGEON_LIST.drag_vector = DraggableList.drag_vector
            DUNGEON_LIST.ocr_class = OcrDungeonList
            DUNGEON_LIST.load_rows(main=self)
            # Check if dungeon unlocked
            for entrance in DUNGEON_LIST.navigates:
                if entrance == dungeon:
                    logger.error(f'Trying to enter dungeon {dungeon}, but teleport is not unlocked')
                    return False

        return True

    def _dungeon_enter(self, dungeon, enter_check_button=COMBAT_PREPARE, skip_first_screenshot=True):
        """
        Pages:
            in: page_guide, Survival_Index, nav including dungeon
            out: COMBAT_PREPARE, FORGOTTEN_HALL_CHECK
        """
        logger.hr('Dungeon enter', level=2)
        skip_first_load = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(enter_check_button):
                logger.info(f'Arrive {enter_check_button.name}')
                break

            # Additional
            pass

            # Click teleport
            if self.appear(page_guide.check_button, interval=1):
                if skip_first_load:
                    skip_first_load = False
                else:
                    DUNGEON_LIST.load_rows(main=self)
                entrance = DUNGEON_LIST.keyword2button(dungeon)
                if entrance is not None:
                    self.device.click(entrance)
                    self.interval_reset(page_guide.check_button)
                    continue
                else:
                    logger.warning(f'Cannot find dungeon entrance of {dungeon}')
                    continue

    def dungeon_goto(self, dungeon: DungeonList):
        """
        Returns:
            bool: If success

        Pages:
            in: page_guide, Survival_Index
            out: COMBAT_PREPARE if success
                page_guide if failed

        Examples:
            from tasks.dungeon.keywords import KEYWORDS_DUNGEON_LIST
            self = DungeonUI('alas')
            self.device.screenshot()
            self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Survival_Index)
            self.dungeon_goto(KEYWORDS_DUNGEON_LIST.Calyx_Crimson_Harmony)
        """
        if dungeon.is_Simulated_Universe:
            self._dungeon_nav_goto(dungeon)
            pass
            self._dungeon_insight(dungeon)
            return True

        # Reset search button
        DUNGEON_LIST.search_button = OCR_DUNGEON_LIST

        if dungeon.is_Calyx_Golden \
                or dungeon.is_Calyx_Crimson \
                or dungeon.is_Stagnant_Shadow \
                or dungeon.is_Cavern_of_Corrosion:
            self._dungeon_nav_goto(dungeon)
            self._dungeon_insight(dungeon)
            self._dungeon_enter(dungeon)
            return True
        if dungeon.is_Forgotten_Hall:
            self._dungeon_nav_goto(dungeon)
            self._dungeon_insight(dungeon)
            self._dungeon_enter(dungeon, enter_check_button=FORGOTTEN_HALL_CHECK)
            return True

        logger.error(f'Goto dungeon {dungeon} is not supported')
        return False
