import numpy as np

from module.base.utils import color_similar, get_color
from module.base.base import ModuleBase
from module.combat.assets import *
from module.combat_ui.assets import *
from module.combat_ui.dictionary import (pause_template, quit_template)
from module.logger import logger
from module.template.assets import TEMPLATE_COMBAT_LOADING
from module.ui.assets import BACK_ARROW, EXERCISE_CHECK, MUNITIONS_CHECK

class CombatUI(ModuleBase):
    theme = None
    
    def is_combat_loading(self):
        """
        Returns:
            bool:
        """
        image = self.image_crop((0, 620, 1280, 720), copy=False)
        similarity, button = TEMPLATE_COMBAT_LOADING.match_luma_result(image)
        if similarity > 0.85:
            loading = (button.area[0] + 38 - LOADING_BAR.area[0]) / (LOADING_BAR.area[2] - LOADING_BAR.area[0])
            logger.attr('Loading', f'{int(loading * 100)}%')
            return True
        else:
            return False

    def _is_combat_executing(self, theme):
        """
        Returns:
            bool:
        """
        if theme == 'Old':  # Old theme uses PAUSE button
            if self.config.SERVER in ['cn', 'en']:
                return PAUSE.match_luma(self.device.image, offset=(10, 10))
            else:
                color = get_color(self.device.image, PAUSE.area)
                if color_similar(color, PAUSE.color) or color_similar(color, (238, 244, 248)):
                    if np.max(self.image_crop(PAUSE_DOUBLE_CHECK, copy=False)) < 153:
                        return True
                return False
        else:
            return pause_template[theme].match_template_color(self.device.image, offset=(10, 10))

    def is_combat_executing(self):
        """
        Returns:
            Button: PAUSE button that appears
        """
        self.device.stuck_record_add(PAUSE)
        if self.theme is not None:
            if self._is_combat_executing(self.theme):
                return pause_template[self.theme]
            return False
        else:
            for theme, button in pause_template.items():
                if self._is_combat_executing(theme):
                    logger.info(f"Battle UI is detected as {theme}")
                    self.theme = theme
                    return button
            return False
    
    def handle_combat_quit(self, offset=(20, 20), interval=3):
        timer = self.get_interval_timer(QUIT, interval=interval)
        if not timer.reached():
            return False
        if self.theme is not None:
            quit_button = quit_template[self.theme]
            if quit_button.match_luma(self.device.image, offset=offset):
                self.device.click(quit_button)
                timer.reset()
                return True
        else:
            for button in set(quit_template.values()):
                if button.match_luma(self.device.image, offset=offset):
                    self.device.click(button)
                    timer.reset()
                    return True
        return False
    
    def ensure_combat_oil_loaded(self):
        self.wait_until_stable(COMBAT_OIL_LOADING)

    def handle_combat_automation_confirm(self):
        if self.appear(AUTOMATION_CONFIRM_CHECK, threshold=30, interval=1):
            self.appear_then_click(AUTOMATION_CONFIRM, offset=(20, 20))
            return True
        return False

    def handle_battle_preparation(self):
        """
        Returns:
            bool:
        """
        if self.appear_then_click(BATTLE_PREPARATION, offset=(20, 20), interval=2):
            return True
        return False
    
    def handle_battle_status(self, drop=None):
        """
        Args:
            drop (DropImage):

        Returns:
            bool:
        """
        if self.is_combat_executing():
            return False
        if self.appear(BATTLE_STATUS_S, interval=self.battle_status_click_interval):
            if drop:
                drop.handle_add(self)
            else:
                self.device.sleep((0.25, 0.5))
            self.device.click(BATTLE_STATUS_S)
            return True
        if self.appear(BATTLE_STATUS_A, interval=self.battle_status_click_interval):
            logger.warning('Battle status A')
            if drop:
                drop.handle_add(self)
            else:
                self.device.sleep((0.25, 0.5))
            self.device.click(BATTLE_STATUS_A)
            return True
        if self.appear(BATTLE_STATUS_B, interval=self.battle_status_click_interval):
            logger.warning('Battle Status B')
            if drop:
                drop.handle_add(self)
            else:
                self.device.sleep((0.25, 0.5))
            self.device.click(BATTLE_STATUS_B)
            return True
        if self.appear(BATTLE_STATUS_C, interval=self.battle_status_click_interval):
            logger.warning('Battle Status C')
            # raise GameStuckError('Battle status C')
            if drop:
                drop.handle_add(self)
            else:
                self.device.sleep((0.25, 0.5))
            self.device.click(BATTLE_STATUS_C)
            return True
        if self.appear(BATTLE_STATUS_D, interval=self.battle_status_click_interval):
            logger.warning('Battle Status D')
            # raise GameStuckError('Battle Status D')
            if drop:
                drop.handle_add(self)
            else:
                self.device.sleep((0.25, 0.5))
            self.device.click(BATTLE_STATUS_D)
            return True

        return False

    def handle_get_items(self, drop=None):
        """
        Args:
            drop (DropImage):

        Returns:
            bool:
        """
        if self.appear(GET_ITEMS_1, offset=5, interval=self.battle_status_click_interval):
            if drop:
                drop.handle_add(self)
            self.device.click(GET_ITEMS_1)
            self.interval_reset(BATTLE_STATUS_S)
            self.interval_reset(BATTLE_STATUS_A)
            self.interval_reset(BATTLE_STATUS_B)
            return True
        if self.appear(GET_ITEMS_2, offset=5, interval=self.battle_status_click_interval):
            if drop:
                drop.handle_add(self)
            self.device.click(GET_ITEMS_1)
            self.interval_reset(BATTLE_STATUS_S)
            self.interval_reset(BATTLE_STATUS_A)
            self.interval_reset(BATTLE_STATUS_B)
            return True
        if self.appear(GET_ITEMS_3, offset=5, interval=self.battle_status_click_interval):
            if drop:
                drop.handle_add(self)
            self.device.click(GET_ITEMS_1)
            self.interval_reset(BATTLE_STATUS_S)
            self.interval_reset(BATTLE_STATUS_A)
            self.interval_reset(BATTLE_STATUS_B)
            return True

        return False

    def handle_exp_info(self):
        """
        Returns:
            bool:
        """
        if self.is_combat_executing():
            return False
        if self.appear_then_click(EXP_INFO_S):
            self.device.sleep((0.25, 0.5))
            return True
        if self.appear_then_click(EXP_INFO_A):
            self.device.sleep((0.25, 0.5))
            return True
        if self.appear_then_click(EXP_INFO_B):
            self.device.sleep((0.25, 0.5))
            return True

        return False

    def handle_get_ship(self, drop=None):
        """
        Args:
            drop (DropImage):

        Returns:
            bool:
        """
        if self.appear_then_click(GET_SHIP, interval=1):
            if self.appear(NEW_SHIP):
                logger.info('Get a new SHIP')
                if drop:
                    drop.handle_add(self)
                self.config.GET_SHIP_TRIGGERED = True
            return True

        return False

    def handle_combat_mis_click(self):
        """
        Returns:
            bool:
        """
        if self.appear(MUNITIONS_CHECK, offset=(20, 20), interval=5):
            logger.info(f'{MUNITIONS_CHECK} -> {BACK_ARROW}')
            self.device.click(BACK_ARROW)
            return True
        if self.appear(EXERCISE_CHECK, offset=(20, 20), interval=5):
            logger.info(f'{EXERCISE_CHECK} -> {BACK_ARROW}')
            self.device.click(BACK_ARROW)
            return True

        return False
