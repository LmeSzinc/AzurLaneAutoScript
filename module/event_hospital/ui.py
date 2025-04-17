from module.combat.assets import BATTLE_PREPARATION
from module.event_hospital.assets import *
from module.logger import logger
from module.minigame.assets import BACK
from module.raid.assets import RAID_FLEET_PREPARATION
from module.ui.page import page_hospital
from module.ui.ui import UI


class HospitalUI(UI):
    def is_in_clue(self, interval=0):
        return self.appear(HOSIPITAL_CLUE_CHECK, offset=(20, 20), interval=interval)

    def handle_get_clue(self):
        """
        Returns:
            bool: If clicked
        """
        if self.appear_then_click(GET_CLUE, offset=(20, 20), interval=1):
            return True
        return False

    def handle_clue_exit(self):
        """
        Returns:
            bool: If clicked
        """
        if self.appear_then_click(HOSPITAL_BATTLE_EXIT, offset=(20, 20), interval=2):
            return True
        if self.ui_page_appear(page_hospital, interval=2):
            logger.info(f'{page_hospital} -> {HOSIPITAL_GOTO_CLUE}')
            self.device.click(HOSIPITAL_GOTO_CLUE)
            return True
        if self.appear(BATTLE_PREPARATION, offset=(30, 20), interval=2):
            logger.info(f'{BATTLE_PREPARATION} -> {BACK}')
            self.device.click(BACK)
            return True
        if self.appear(RAID_FLEET_PREPARATION, offset=(30, 30), interval=2):
            logger.info(f'{RAID_FLEET_PREPARATION} -> {BACK}')
            self.device.click(BACK)
            return True
        if self.handle_get_clue():
            return True
        return False
