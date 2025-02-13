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
        elif theme in ['New', 'Neon', 'Cyber', 'HolyLight']:
            return pause_template[theme].match_template_color(self.device.image, offset=(10, 10))
        elif theme in ['Iridescent_Fantasy', 'Christmas']:
            return pause_template[theme].match_luma(self.device.image, offset=(10, 10))
        else:
            logger.warning(f'Unknown combat ui theme {theme}')
            return False

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

    def _handle_combat_quit(self, button, offset=(20, 20)):
        if button.match_luma(self.device.image, offset=offset):
            self.device.click(button)
            return True
        return False

    def handle_combat_quit(self, offset=(20, 20), interval=3):
        timer = self.get_interval_timer(QUIT, interval=interval)
        if not timer.reached():
            return False
        if self.theme is not None:
            quit_button = quit_template[self.theme]
            if self._handle_combat_quit(quit_button, offset=offset):
                timer.reset()
                return True
        else:
            for button in quit_template.values():
                if self._handle_combat_quit(button, offset=offset):
                    timer.reset()
                    return True
        return False