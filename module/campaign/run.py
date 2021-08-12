import copy
import importlib
import os
from datetime import datetime

from module.campaign.assets import *
from module.campaign.campaign_base import CampaignBase
from module.config.config import AzurLaneConfig, ConfigBackup
from module.exception import ScriptEnd
from module.logger import logger
from module.ocr.ocr import Digit
from module.reward.reward import Reward

OCR_OIL = Digit(OCR_OIL, name='OCR_OIL', letter=(247, 247, 247), threshold=128)


class CampaignRun(Reward):
    folder: str
    name: str
    stage: str
    module = None
    config: AzurLaneConfig
    campaign: CampaignBase
    run_count: int

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
        if folder.startswith('event') or folder.startswith('war_archives'):
            self.stage = name

        try:
            self.module = importlib.import_module('.' + name, f'campaign.{folder}')
        except ModuleNotFoundError:
            logger.warning(f'Map file not found: campaign.{folder}.{name}')
            folder = f'./campaign/{folder}'
            if not os.path.exists(folder):
                logger.warning(f'Folder not exists: {folder}')
            else:
                files = [f[:-3] for f in os.listdir(folder) if f[-3:] == '.py']
                logger.warning(f'Existing files: {files}')
            exit(1)

        config = copy.copy(self.config).merge(self.module.Config())
        device = self.device
        self.campaign = self.module.Campaign(config=config, device=device)
        self.campaign_name_set(name)

        return True

    def campaign_name_set(self, name):
        """
        Args:
            name (str): Campaign name used in drop screenshot.

        Returns:
            list[ConfigBackup]:
        """
        if not self.campaign.config.ENABLE_SAVE_GET_ITEMS \
                or not len(self.campaign.config.SCREEN_SHOT_SAVE_FOLDER_BASE.strip()):
            return []
        # Create folder to save drop screenshot
        folder = self.campaign.config.SCREEN_SHOT_SAVE_FOLDER_BASE + '/' + name
        if not os.path.exists(folder):
            os.mkdir(folder)

        backup1 = self.campaign.config.cover(SCREEN_SHOT_SAVE_FOLDER=folder)
        backup2 = self.config.cover(SCREEN_SHOT_SAVE_FOLDER=folder)
        return [backup1, backup2]

    def triggered_stop_condition(self, oil_check=True):
        """
        Returns:
            bool: If triggered a stop condition.
        """
        # Run count limit
        if self.run_count >= self.config.STOP_IF_COUNT_GREATER_THAN > 0:
            logger.hr('Triggered count stop')
            self.device.send_notification('Triggered Stop Condition', 'Triggered count stop')
            return True
        # Run time limit
        if self.config.STOP_IF_TIME_REACH and datetime.now() > self.config.STOP_IF_TIME_REACH:
            logger.hr('Triggered time limit')
            self.device.send_notification('Triggered Stop Condition', 'Triggered time limit')
            self.config.config.set('Setting', 'if_time_reach', '0')
            self.config.save()
            return True
        # Dock full limit
        if self.config.STOP_IF_DOCK_FULL and self.campaign.config.DOCK_FULL_TRIGGERED:
            logger.hr('Triggered dock full limit')
            self.device.send_notification('Triggered Stop Condition', 'Triggered dock full limit')
            return True
        # Emotion limit
        if self.config.STOP_IF_TRIGGER_EMOTION_LIMIT and self.campaign.config.EMOTION_LIMIT_TRIGGERED:
            logger.hr('Triggered emotion limit')
            self.device.send_notification('Triggered Stop Condition', 'Triggered emotion limit')
            return True
        # Lv120 limit
        if self.config.STOP_IF_REACH_LV120 and self.campaign.config.LV120_TRIGGERED:
            logger.hr('Triggered lv120 limit')
            self.device.send_notification('Triggered Stop Condition', 'Triggered lv120 limit')
            return True
        # Oil limit
        if oil_check and self.config.STOP_IF_OIL_LOWER_THAN:
            if OCR_OIL.ocr(self.device.image) < self.config.STOP_IF_OIL_LOWER_THAN:
                logger.hr('Triggered oil limit')
                self.device.send_notification('Triggered Stop Condition', 'Triggered oil limit')
                return True
        # If Get a New Ship
        if self.config.STOP_IF_GET_SHIP and self.campaign.config.GET_SHIP_TRIGGERED:
            logger.hr('Triggered get ship')
            self.device.send_notification('Triggered Stop Condition', 'Triggered get ship')
            return True

        return False

    def _triggered_app_restart(self):
        """
        Returns:
            bool: If triggered a restart condition.
        """
        if self.config.triggered_app_restart():
            return True
        if not self.campaign.config.IGNORE_LOW_EMOTION_WARN:
            if self.campaign.emotion.triggered_bug():
                logger.hr('Triggered restart avoid emotion bug')
                self.device.send_notification('Triggered App Restart', 'Triggered restart avoid emotion bug')
                return True

        return False

    def handle_app_restart(self):
        if self._triggered_app_restart():
            self.app_restart()
            return True

        return False

    @staticmethod
    def handle_stage_name(name, folder):
        """
        Handle wrong stage names.
        In some events, the name of SP may be different, such as 'vsp', muse sp.
        To call them easier, their map files should named 'sp.py'.

        Args:
            name (str): Name of .py file.
            folder (str): Name of the file folder under campaign.

        Returns:
            str, str: name, folder
        """
        if folder == 'event_20201126_cn' and name == 'vsp':
            name = 'sp'
        if folder == 'event_20210723_cn' and name == 'vsp':
            name = 'sp'

        return name, folder

    def run(self, name, folder='campaign_main', total=0):
        """
        Args:
            name (str): Name of .py file.
            folder (str): Name of the file folder under campaign.
            total (int):
        """
        name, folder = self.handle_stage_name(name, folder)
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
            elif self.campaign.is_in_auto_search_menu():
                logger.info('In auto search menu, skip ensure_campaign_ui.')
            else:
                self.campaign.ensure_campaign_ui(
                    name=self.stage,
                    mode=self.config.CAMPAIGN_MODE if self.config.COMMAND.lower() == 'main' else 'normal'
                )
            if self.config.ENABLE_REWARD and self.commission_notice_show_at_campaign():
                logger.info('Commission notice found')
                if self.reward():
                    self.campaign.fleet_checked_reset()
                    continue

            # End
            if self.triggered_stop_condition(oil_check=not self.campaign.is_in_auto_search_menu()):
                self.campaign.ensure_auto_search_exit()
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
            # One-time stage limit
            if self.campaign.config.MAP_IS_ONE_TIME_STAGE:
                if self.run_count >= 1:
                    logger.hr('Triggered one-time stage limit')
                    break

        self.campaign.ensure_auto_search_exit()
