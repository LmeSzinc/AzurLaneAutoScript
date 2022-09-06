from module.base.utils import image_left_strip
from module.combat.combat import BATTLE_PREPARATION, Combat
from module.logger import logger
from module.ocr.ocr import DigitCounter
from module.os_ash.assets import *
from module.os_handler.assets import IN_MAP
from module.os_handler.map_event import MapEventHandler
from module.ui.assets import BACK_ARROW
from module.ui.ui import UI


class DailyDigitCounter(DigitCounter):
    def pre_process(self, image):
        image = super().pre_process(image)
        image = image_left_strip(image, threshold=120, length=35)
        return image


class AshBeaconFinished(Exception):
    pass


class AshCombat(Combat):
    def handle_battle_status(self, drop=None):
        """
        Args:
            drop (DropImage):

        Returns:
            bool:
        """
        if self.is_combat_executing():
            return False
        if super().handle_battle_status(drop=drop):
            return True
        if self.appear(BATTLE_STATUS, offset=(20, 20), interval=self.battle_status_click_interval):
            if drop:
                drop.handle_add(self)
            else:
                self.device.sleep((0.25, 0.5))
            self.device.click(BATTLE_STATUS)
            return True
        if self.appear(BATTLE_PREPARATION, offset=(30, 30), interval=3):
            self.device.click(BACK_ARROW)
            return True

        return False

    def handle_battle_preparation(self):
        if super().handle_battle_preparation():
            return True

        if self.appear_then_click(ASH_START, offset=(30, 30)):
            return True
        if self.handle_get_items():
            return True
        if self.appear(BEACON_REWARD):
            logger.info("Ash beacon already finished.")
            raise AshBeaconFinished
        if self.appear(BEACON_EMPTY, offset=(20, 20)):
            logger.info("Ash beacon already empty.")
            raise AshBeaconFinished

        return False

    def combat(self, *args, **kwargs):
        try:
            super().combat(*args, **kwargs)
        except AshBeaconFinished:
            pass


class OSAsh(UI, MapEventHandler):

    def is_in_map(self):
        return self.appear(IN_MAP, offset=(200, 5))

    _ash_fully_collected = False

    def ash_collect_status(self):
        """
        Returns:
            int: 0 to 100.
        """
        if self._ash_fully_collected:
            return 0
        if self.image_color_count(ASH_COLLECT_STATUS, color=(235, 235, 235), threshold=221, count=20):
            logger.info('Ash beacon status: light')
            ocr_collect = DigitCounter(
                ASH_COLLECT_STATUS, letter=(235, 235, 235), threshold=160, name='OCR_ASH_COLLECT_STATUS')
            ocr_daily = DailyDigitCounter(
                ASH_DAILY_STATUS, letter=(235, 235, 235), threshold=160, name='OCR_ASH_DAILY_STATUS')
        elif self.image_color_count(ASH_COLLECT_STATUS, color=(140, 142, 140), threshold=221, count=20):
            logger.info('Ash beacon status: gray')
            ocr_collect = DigitCounter(
                ASH_COLLECT_STATUS, letter=(140, 142, 140), threshold=160, name='OCR_ASH_COLLECT_STATUS')
            ocr_daily = DailyDigitCounter(
                ASH_DAILY_STATUS, letter=(140, 142, 140), threshold=160, name='OCR_ASH_DAILY_STATUS')
        else:
            # If OS daily mission received or finished, the popup will cover beacon status.
            logger.info('Ash beacon status is covered, will check next time')
            return 0

        status, _, _ = ocr_collect.ocr(self.device.image)
        daily, _, _ = ocr_daily.ocr(self.device.image)

        if daily >= 200:
            logger.info('Ash beacon fully collected today')
            self._ash_fully_collected = True

        if status < 0:
            status = 0
        return status

    def handle_ash_beacon_attack(self):
        """
        Returns:
            bool: If attacked.

        Pages:
            in: is_in_map
            out: is_in_map
        """
        if not self.config.OpsiAshBeacon_AshAttack \
                and not self.config.OpsiDossierBeacon_Enable:
            return False

        if self.ash_collect_status() < 100:
            return False

        self.config.task_call(task='OpsiAshBeacon')
        return True
