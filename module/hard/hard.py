import importlib

from campaign.campaign_hard.campaign_hard import Campaign
from module.campaign.run import CampaignRun
from module.hard.assets import *
from module.logger import logger
from module.ocr.ocr import Digit

OCR_HARD_REMAIN = Digit(OCR_HARD_REMAIN, letter=(123, 227, 66), threshold=128, alphabet='0123')
RECORD_OPTION = ('DailyRecord', 'hard')
RECORD_SINCE = (0,)


class CampaignHard(CampaignRun):
    equipment_has_take_on = False
    campaign: Campaign

    def run(self):
        logger.hr('Campaign hard', level=1)
        chapter, stage = self.config.HARD_CAMPAIGN.split('-')
        name = f'campaign_{chapter}_{stage}'
        self.reward_backup_daily_reward_settings()
        hard_config = self.config.cover(
            CAMPAIGN_MODE='hard',
            ENABLE_MAP_FLEET_LOCK=True,
            ENABLE_AUTO_SEARCH=True,
            AUTO_SEARCH_SETTING='fleet1_all_fleet2_standby' if self.config.FLEET_HARD == 1 else 'fleet1_standby_fleet2_all',
        )

        # Initial
        self.load_campaign(name='campaign_hard', folder='campaign_hard')  # Load campaign file
        module = importlib.import_module('.' + name, 'campaign.campaign_main')  # Load map from normal mode.
        self.campaign.MAP = module.MAP
        backups = self.campaign_name_set(name + '_HARD')
        if self.equipment_has_take_on:
            self.campaign.equipment_has_take_on = True

        # UI ensure
        self.ui_weigh_anchor()
        self.campaign.ensure_campaign_ui(self.config.HARD_CAMPAIGN, mode='hard')

        # Run
        remain = OCR_HARD_REMAIN.ocr(self.device.image)
        logger.attr('Remain', remain)
        for n in range(remain):
            self.campaign.run()

        self.campaign.ensure_auto_search_exit()

        for backup in backups:
            backup.recover()
        self.campaign.equipment_take_off_when_finished()
        hard_config.recover()
        self.reward_recover_daily_reward_settings()

    def record_executed_since(self):
        return self.config.record_executed_since(option=RECORD_OPTION, since=RECORD_SINCE)

    def record_save(self):
        return self.config.record_save(option=RECORD_OPTION)
