import copy
import importlib
import os

from module.campaign.assets import *
from module.campaign.campaign_base import CampaignBase
from module.combat.auto_search_combat import AutoSearchCombat
from module.config.config import AzurLaneConfig
from module.config.utils import deep_get
from module.exception import RequestHumanTakeover, ScriptEnd
from module.logger import logger
from module.ocr.ocr import Digit
from module.ui.ui import UI

OCR_OIL = Digit(OCR_OIL, name='OCR_OIL', letter=(247, 247, 247), threshold=128)


class CampaignRun(UI):
    folder: str
    name: str
    stage: str
    module = None
    config: AzurLaneConfig
    campaign: CampaignBase
    run_count: int
    run_limit: int

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

            logger.critical('Please update Alas')
            logger.critical('If file is still missing after update, '
                            'contact developers, or make map files yourself using dev_tools/map_extractor.py')
            raise RequestHumanTakeover

        config = copy.copy(self.config).merge(self.module.Config())
        device = self.device
        self.campaign = self.module.Campaign(config=config, device=device)

        return True

    def triggered_stop_condition(self, oil_check=True):
        """
        Returns:
            bool: If triggered a stop condition.
        """
        # Run count limit
        if self.run_limit and self.config.StopCondition_RunCount <= 0:
            logger.hr('Triggered stop condition: Run count')
            self.config.StopCondition_RunCount = 0
            self.config.Scheduler_Enable = False
            return True
        # Lv120 limit
        if self.config.StopCondition_ReachLevel120 and self.campaign.config.LV120_TRIGGERED:
            logger.hr('Triggered stop condition: Reach level 120')
            self.config.Scheduler_Enable = False
            return True
        # Oil limit
        if oil_check and self.config.StopCondition_OilLimit:
            if OCR_OIL.ocr(self.device.image) < self.config.StopCondition_OilLimit:
                logger.hr('Triggered stop condition: Oil limit')
                self.config.task_delay(minute=(120, 240))
                return True
        # Auto search oil limit
        if self.campaign.auto_search_oil_limit_triggered:
            logger.hr('Triggered stop condition: Auto search oil limit')
            self.config.task_delay(minute=(120, 240))
            return True
        # If Get a New Ship
        if self.config.StopCondition_GetNewShip and self.campaign.config.GET_SHIP_TRIGGERED:
            logger.hr('Triggered stop condition: Get new ship')
            self.config.Scheduler_Enable = False
            return True

        return False

    def _triggered_app_restart(self):
        """
        Returns:
            bool: If triggered a restart condition.
        """
        if not self.campaign.config.Emotion_IgnoreLowEmotionWarn:
            if self.campaign.emotion.triggered_bug():
                logger.info('Triggered restart avoid emotion bug')
                return True

        return False

    def handle_app_restart(self):
        if self._triggered_app_restart():
            self.config.task_call('Restart')
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
        name = name.lower()
        if name[0].isdigit():
            name = 'campaign_' + name.lower().replace('-', '_')
        if folder == 'event_20201126_cn' and name == 'vsp':
            name = 'sp'
        if folder == 'event_20210723_cn' and name == 'vsp':
            name = 'sp'

        return name, folder

    def handle_commission_notice(self):
        """
        Check commission notice.
        If found, stop current task and call commission.

        Raises:
            TaskEnd: If found commission notice.

        Pages:
            in: page_campaign
        """
        if deep_get(self.config.data, keys='Commission.Scheduler.Enable', default=False):
            if self.campaign.commission_notice_show_at_campaign():
                logger.info('Commission notice found')
                self.config.task_call('Commission')
                self.config.task_stop('Commission notice found')

    def run(self, name, folder='campaign_main', mode='normal', total=0):
        """
        Args:
            name (str): Name of .py file.
            folder (str): Name of the file folder under campaign.
            mode (str): `normal` or `hard`
            total (int):
        """
        name, folder = self.handle_stage_name(name, folder)
        self.load_campaign(name, folder=folder)
        self.run_count = 0
        self.run_limit = self.config.StopCondition_RunCount
        while 1:
            # End
            if total and self.run_count >= total:
                break

            # Log
            logger.hr(name, level=1)
            if self.config.StopCondition_RunCount > 0:
                logger.info(f'Count remain: {self.config.StopCondition_RunCount}')
            else:
                logger.info(f'Count: {self.run_count}')

            # UI ensure
            self.device.screenshot()
            self.campaign.device.image = self.device.image
            if self.campaign.is_in_map():
                logger.info('Already in map, skip ensure_campaign_ui.')
            elif self.campaign.is_in_auto_search_menu():
                logger.info('In auto search menu, skip ensure_campaign_ui.')
            else:
                self.ui_get_current_page()
                self.campaign.ensure_campaign_ui(
                    name=self.stage,
                    mode=mode
                )
            self.handle_commission_notice()

            # End
            if self.triggered_stop_condition(oil_check=not self.campaign.is_in_auto_search_menu()):
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
            if self.config.StopCondition_RunCount:
                self.config.StopCondition_RunCount -= 1
            # End
            if self.triggered_stop_condition(oil_check=False):
                break
            # One-time stage limit
            if self.campaign.config.MAP_IS_ONE_TIME_STAGE:
                if self.run_count >= 1:
                    logger.hr('Triggered one-time stage limit')
                    break
            # Scheduler
            if self.config.task_switched():
                self.campaign.ensure_auto_search_exit()
                self.config.task_stop()

        self.campaign.ensure_auto_search_exit()
