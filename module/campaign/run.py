import copy
import importlib
import os
from datetime import datetime

from module.base.ocr import Digit
from module.campaign.assets import *
from module.campaign.campaign_base import CampaignBase
from module.campaign.campaign_ui import CampaignUI
from module.config.config import AzurLaneConfig
from module.logger import logger

OCR_OIL = Digit(OCR_OIL, letter=(247, 247, 247), back=(33, 36, 49), limit=25000, name='OCR_OIL')


class CampaignRun(CampaignUI):
    folder: str
    name: str
    stage: str
    module = None
    config: AzurLaneConfig
    campaign: CampaignBase

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
        # self.config.CAMPAIGN_NAME = name
        # folder = self.config.SCREEN_SHOT_SAVE_FOLDER_BASE + '/' + name
        # if not os.path.exists(folder):
        #     os.mkdir(folder)
        # self.config.SCREEN_SHOT_SAVE_FOLDER = folder

        folder = self.campaign.config.SCREEN_SHOT_SAVE_FOLDER_BASE + '/' + name
        if not os.path.exists(folder):
            os.mkdir(folder)
        self.campaign.config.SCREEN_SHOT_SAVE_FOLDER = folder

    def oil_check(self):
        """
        Returns:
            bool: If have enough oil.
        """
        if not self.config.STOP_IF_OIL_LOWER_THAN:
            return True
        self.device.screenshot()
        return OCR_OIL.ocr(self.device.image) > self.config.STOP_IF_OIL_LOWER_THAN

    def run(self, name, folder='campaign_main'):
        """
        Args:
            name (str): Name of .py file.
            folder (str): Name of the file folder under campaign.
        """
        self.load_campaign(name, folder=folder)
        n = 0
        while 1:
            # End
            if n >= self.config.STOP_IF_COUNT_GREATER_THAN > 0:
                logger.hr('Triggered count stop')
                break
            if not self.oil_check():
                logger.hr('Triggered oil limit')
                break
            if self.config.STOP_IF_TIME_REACH and datetime.now() > self.config.STOP_IF_TIME_REACH:
                logger.hr('Triggered time limit')
                self.config.config.set('Setting', 'if_time_reach', '0')
                self.config.save()
                break
            if self.config.STOP_IF_TRIGGER_EMOTION_LIMIT and self.campaign.config.EMOTION_LIMIT_TRIGGERED:
                logger.hr('Triggered emotion limit')
                break

            # Log
            logger.hr(name, level=1)
            if self.config.STOP_IF_COUNT_GREATER_THAN > 0:
                logger.info(f'Count: [{n}/{self.config.STOP_IF_COUNT_GREATER_THAN}]')
            else:
                logger.info(f'Count: [{n}]')

            # Run
            self.ensure_campaign_ui(name=self.stage)
            self.campaign.ENTRANCE = self.campaign_get_entrance(name=self.stage)
            self.campaign.run()

            # After run
            n += 1
            if self.config.STOP_IF_COUNT_GREATER_THAN > 0:
                count = self.config.STOP_IF_COUNT_GREATER_THAN - n
                count = 0 if count < 0 else count
                self.config.config.set('Setting', 'if_count_greater_than', str(count))
                self.config.save()
