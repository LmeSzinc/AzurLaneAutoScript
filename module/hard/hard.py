import importlib

from campaign.campaign_hard.campaign_hard import Campaign
from module.campaign.run import CampaignRun
from module.exception import CampaignEnd, ScriptEnd
from module.hard.assets import *
from module.logger import logger
from module.ocr.ocr import Digit

OCR_HARD_REMAIN = Digit(OCR_HARD_REMAIN, letter=(123, 227, 66), threshold=128, alphabet='0123')


class CampaignHard(CampaignRun):
    equipment_has_take_on = False
    campaign: Campaign

    def run(self):
        logger.hr('Campaign hard', level=1)
        chapter, stage = self.config.Hard_HardStage.split('-')
        name = f'campaign_{chapter}_{stage}'
        self.config.override(
            Campaign_Mode='hard',
            Campaign_UseFleetLock=True,
            Campaign_UseAutoSearch=True,
        )
        # Equipment take on
        # campaign/campaign_hard/campaign_hard.py Campaign.fleet_preparation()

        # Initial
        self.load_campaign(name='campaign_hard', folder='campaign_hard')  # Load campaign file
        module = importlib.import_module('.' + name, 'campaign.campaign_main')  # Load map from normal mode.
        self.campaign.MAP = module.MAP

        # UI ensure
        self.device.click_record_clear()
        if not hasattr(self.device, 'image') or self.device.image is None:
            self.device.screenshot()
        self.campaign.device.image = self.device.image
        if self.campaign.is_in_map():
            logger.info('Already in map, retreating.')
            try:
                self.campaign.withdraw()
            except CampaignEnd:
                pass
            self.campaign.ensure_campaign_ui(name=self.config.Hard_HardStage, mode='hard')
        elif self.campaign.is_in_auto_search_menu():
            if self.can_use_auto_search_continue():
                    logger.info('In auto search menu, skip ensure_campaign_ui.')
            else:
                logger.info('In auto search menu, closing.')
                self.campaign.ensure_auto_search_exit()
                self.campaign.ensure_campaign_ui(name=self.config.Hard_HardStage, mode='hard')
        else:
            self.campaign.ensure_campaign_ui(name=self.config.Hard_HardStage, mode='hard')
        self.handle_commission_notice()
        
        # Run
        remain = OCR_HARD_REMAIN.ocr(self.device.image)
        logger.attr('Remain', remain)
        for n in range(remain):
            try:
                self.campaign.run()
            except ScriptEnd as e:
                logger.hr('Script end')
                logger.info(str(e))
                break

        self.campaign.ensure_auto_search_exit()
        # self.campaign.equipment_take_off_when_finished()

        # Scheduler
        self.config.task_delay(server_update=True)
        self.config.task_call('Reward')
