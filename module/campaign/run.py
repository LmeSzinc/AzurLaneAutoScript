import copy
import importlib
import os
from datetime import datetime

from module.base.ocr import Digit
from module.campaign.assets import *
from module.campaign.campaign_base import CampaignBase
from module.campaign.campaign_ui import CampaignUI
from module.config.config import AzurLaneConfig
from module.handler.login import LoginHandler
from module.logger import logger
from module.exception import ScriptEnd, CampaignNameError
from module.reward.reward import Reward

OCR_OIL = Digit(OCR_OIL, letter=(247, 247, 247), back=(33, 36, 49), limit=25000, name='OCR_OIL')


class CampaignRun(CampaignUI, Reward, LoginHandler):
    folder: str
    name: str
    stage: str
    module = None
    config: AzurLaneConfig
    campaign: CampaignBase
    run_count: int
    start_time = datetime.now()

    def load_campaign(self, name, folder='campaign_main'):
        """
        Args:
            name (str): Name of .py file under module.campaign.
            folder (str): Name of the file folder under campaign.

        Returns:
            bool: If load.
        """
        if hasattr(self, 'name') and name == self.name:
            return False

        self.name = name
        self.folder = folder

        if folder.startswith('campaign_'):
            self.stage = '-'.join(name.split('_')[1:3])
        if folder.startswith('event'):
            self.stage = name

        self.module = importlib.import_module('.' + name, f'campaign.{folder}')
        config = copy.copy(self.config).merge(self.module.Config())
        device = copy.copy(self.device)
        device.config = config
        self.campaign = self.module.Campaign(config=config, device=device)
        self.campaign_name_set(name)

        # self.config = self.config.merge(self.module.Config())
        # self.campaign_name_set(name)
        # self.device.config = self.config
        # self.campaign = self.module.Campaign(config=self.config, device=self.device)

        return True

    def campaign_name_set(self, name):
        if not self.campaign.config.ENABLE_SAVE_GET_ITEMS \
                or not len(self.campaign.config.SCREEN_SHOT_SAVE_FOLDER_BASE.strip()):
            return False
        # Create folder to save drop screenshot
        folder = self.campaign.config.SCREEN_SHOT_SAVE_FOLDER_BASE + '/' + name
        if not os.path.exists(folder):
            os.mkdir(folder)
        self.campaign.config.SCREEN_SHOT_SAVE_FOLDER = folder

    def triggered_stop_condition(self):
        """

        Returns:
            bool: If triggered a stop condition.
        """
        # Run count limit
        if self.run_count >= self.config.STOP_IF_COUNT_GREATER_THAN > 0:
            logger.hr('Triggered count stop')
            return True
        # Run time limit
        if self.config.STOP_IF_TIME_REACH and datetime.now() > self.config.STOP_IF_TIME_REACH:
            logger.hr('Triggered time limit')
            self.config.config.set('Setting', 'if_time_reach', '0')
            self.config.save()
            return True
        # Dock full limit
        if self.config.STOP_IF_DOCK_FULL and self.campaign.config.DOCK_FULL_TRIGGERED:
            logger.hr('Triggered dock full limit')
            return True
        # Emotion limit
        if self.config.STOP_IF_TRIGGER_EMOTION_LIMIT and self.campaign.config.EMOTION_LIMIT_TRIGGERED:
            logger.hr('Triggered emotion limit')
            return True
        # Oil limit
        if self.config.STOP_IF_OIL_LOWER_THAN:
            if OCR_OIL.ocr(self.device.image) < self.config.STOP_IF_OIL_LOWER_THAN:
                logger.hr('Triggered oil limit')
                return True

        return False

    def _triggered_app_restart(self):
        """
        Returns:
            bool: If triggered a restart condition.
        """
        if self.config.get_server_last_update(since=(0,)) > self.start_time:
            logger.hr('Triggered restart new day')
            return True
        if not self.campaign.config.IGNORE_LOW_EMOTION_WARN:
            if self.campaign.emotion.triggered_bug():
                logger.hr('Triggered restart avoid emotion bug')
                return True

        return False

    def handle_app_restart(self):
        if self._triggered_app_restart():
            self.app_restart()
            self.start_time = datetime.now()
            return True

        return False

    def run(self, name, folder='campaign_main', total=0):
        """
        Args:
            name (str): Name of .py file.
            folder (str): Name of the file folder under campaign.
            total (int):
        """
        self.load_campaign(name, folder=folder)
        self.run_count = 0
        while 1:
            if self.handle_app_restart():
                self.campaign.fleet_checked_reset()
            if self.handle_reward():
                self.campaign.fleet_checked_reset()

            # End
            if total and self.run_count == total:
                break

            # Log
            logger.hr(name, level=1)
            if self.config.STOP_IF_COUNT_GREATER_THAN > 0:
                logger.info(f'Count: [{self.run_count}/{self.config.STOP_IF_COUNT_GREATER_THAN}]')
            else:
                logger.info(f'Count: [{self.run_count}]')

            # UI ensure
            self.device.screenshot()
            self.campaign.device.image = self.device.image
            if self.campaign.is_in_map():
                logger.info('Already in map, skip ensure_campaign_ui.')
            else:
                self.handle_campaign_ui()
            if self.commission_notice_show_at_campaign():
                if self.reward():
                    self.campaign.fleet_checked_reset()
                    continue

            # End
            if self.triggered_stop_condition():
                break

            # Run
            try:
                self.campaign.run()
            except ScriptEnd as e:
                logger.hr('Script end')
                logger.info(str(e))
                break

            # After run
            self.run_count += 1
            if self.config.STOP_IF_COUNT_GREATER_THAN > 0:
                count = self.config.STOP_IF_COUNT_GREATER_THAN - self.run_count
                count = 0 if count < 0 else count
                self.config.config.set('Setting', 'if_count_greater_than', str(count))
                self.config.save()

    def handle_campaign_ui(self):
        for n in range(20):
            try:
                self.ensure_campaign_ui(name=self.stage)
                self.campaign.ENTRANCE = self.campaign_get_entrance(name=self.stage)
                return True
            except CampaignNameError:
                continue

        logger.warning('Campaign name error')
        raise ScriptEnd('Campaign name error')
