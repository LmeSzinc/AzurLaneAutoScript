from datetime import datetime, timedelta

from module.base.utils import image_left_strip
from module.combat.combat import BATTLE_PREPARATION, Combat
from module.config.utils import DEFAULT_TIME
from module.logger import logger
from module.ocr.ocr import DigitCounter
from module.os_ash.assets import *
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
        if self.appear(BATTLE_PREPARATION, offset=(30, 30), interval=2):
            self.device.click(BACK_ARROW)
            return True

        return False

    def handle_battle_preparation(self):
        from module.gg_handler.assets import OCR_PRE_BATTLE_CHECK
        from module.ocr.ocr import Digit
        self.device.screenshot()
        OCR_CHECK = Digit(OCR_PRE_BATTLE_CHECK,letter=(255, 255, 255),threshold=128)
        ocr=OCR_CHECK.ocr(self.device.image)
        if ocr>=16000 :
            logger.critical('There''s high chance that GG is on, restart to disable it')
            from module.gg_handler.gg_data import gg_data
            gg_data(config=self.config, target='gg_on', value=False).set_data()
            gg_data(config=self.config, target='gg_enable', value=True).set_data()
            self.config.task_call('Restart')
            self.config.task_delay(minute=0.5)
            self.config.task_stop('Restart for sake of safty')

        if super().handle_battle_preparation():
            return True

        if self.appear_then_click(ASH_START, offset=(30, 30), interval=2):
            return True
        if self.handle_get_items():
            return True
        if self.appear(BEACON_REWARD):
            logger.info("Ash beacon already finished.")
            raise AshBeaconFinished
        if self.appear(BEACON_EMPTY, offset=(20, 20)):
            logger.info("Ash beacon already empty.")
            raise AshBeaconFinished
        if self.appear(ASH_SHOWDOWN, offset=(20, 20)):
            logger.info("Ash beacon already at ASH_SHOWDOWN.")
            raise AshBeaconFinished

        return False

    def combat(self, *args, expected_end=None, **kwargs):
        try:
            super().combat(*args, expected_end=expected_end, **kwargs)
        except AshBeaconFinished:
            pass


class OSAsh(UI, MapEventHandler):

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
        elif status >= 200:
            logger.info('Ash beacon data reached the holding limit')
            self._ash_fully_collected = True

        if status < 0:
            status = 0
        return status

    def _support_call_ash_beacon_task(self):
        # AshBeacon next run
        next_run = self.config.cross_get(keys="OpsiAshBeacon.Scheduler.NextRun", default=DEFAULT_TIME)
        # Between the next execution time and the present time is more than 30 minutes
        if next_run - datetime.now() > timedelta(minutes=30):
            return True
        return False

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

        if self.ash_collect_status() >= 100 \
                and self._support_call_ash_beacon_task():
            self.config.task_call(task='OpsiAshBeacon')
            return True

        return False
