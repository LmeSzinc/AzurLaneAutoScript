import numpy as np

from module.base.timer import Timer
from module.base.utils import get_color
from module.logger import logger
from module.ocr.ocr import Ocr
from module.ui.draggable_list import DraggableList
from module.ui.switch import Switch
from tasks.base.page import page_guide
from tasks.base.ui import UI
from tasks.dungeon.assets.assets_dungeon_ui import *
from tasks.dungeon.keywords import DungeonNav, DungeonTab, KEYWORDS_DUNGEON_NAV, KEYWORDS_DUNGEON_TAB


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
DUNGEON_NAV_LIST = DraggableList(
    'DungeonNavList', keyword_class=DungeonNav, ocr_class=Ocr, search_button=OCR_DUNGEON_NAV)


class DungeonUI(UI):
    def dungeon_tab_goto(self, state: DungeonTab):
        """
        Args:
            state:

        Examples:
            self = DungeonUI('alas')
            self.device.screenshot()
            self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Operation_Briefing)
            self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Daily_Training)
            self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Survival_Index)
        """
        self.ui_ensure(page_guide)
        SWITCH_DUNGEON_TAB.set(state, main=self)
        if state == KEYWORDS_DUNGEON_TAB.Daily_Training:
            logger.info(f'Tab goto {state}, wait until loaded')
            self._dungeon_wait_daily_training_loaded()
        elif state == KEYWORDS_DUNGEON_TAB.Survival_Index:
            logger.info(f'Tab goto {state}, wait until loaded')
            self._dungeon_wait_survival_loaded()

    def _dungeon_wait_daily_training_loaded(self, skip_first_screenshot=True):
        timeout = Timer(2, count=4).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Wait daily training loaded timeout')
                break
            color = get_color(self.device.image, DAILY_TRAINING_LOADED.area)
            if np.mean(color) < 128:
                logger.info('Daily training loaded')
                break

    def _dungeon_wait_survival_loaded(self, skip_first_screenshot=True):
        timeout = Timer(2, count=4).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Wait survival index loaded timeout')
                break
            if self.appear(SURVIVAL_INDEX_LOADED):
                logger.info('Survival index loaded')
                break
