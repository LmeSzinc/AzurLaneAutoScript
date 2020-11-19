import numpy as np
from campaign.campaign_war_archives.campaign_base import CampaignBase, CampaignNameError
from module.campaign.run import CampaignRun
from module.ocr.ocr import DigitCounter
from module.war_archives.assets import OCR_DATA_KEY_CAMPAIGN, WAR_ARCHIVES_CAMPAIGN_CHECK, WAR_ARCHIVES_CAMPAIGN_TIMER
from module.logger import logger

DATA_KEY_CAMPAIGN = DigitCounter(OCR_DATA_KEY_CAMPAIGN, letter=(255, 247, 247), threshold=64)
WAR_ARCHIVES_CAMPAIGN_TIMER_THRESHOLD = 102

class CampaignWarArchives(CampaignRun, CampaignBase):
    def handle_reward(self):
        if not hasattr(self.device, 'image'):
           self.device.screenshot()

        # Must be in archives campaign to check for active timer
        # Other pages may throw off this RGB average color check
        if self.appear(WAR_ARCHIVES_CAMPAIGN_CHECK, offset=(20, 20)):
            if np.mean(self.image_area(WAR_ARCHIVES_CAMPAIGN_TIMER)) > WAR_ARCHIVES_CAMPAIGN_TIMER_THRESHOLD:
                logger.info('Campaign is still active, delaying reward check for this run')
                return False
        return super().handle_reward()

    def triggered_stop_condition(self):
        # Must be in archives campaign to OCR check
        if self.appear(WAR_ARCHIVES_CAMPAIGN_CHECK, offset=(20, 20)):
            # Check for 0 data keys left to use
            current, remain, total = DATA_KEY_CAMPAIGN.ocr(self.device.image)
            logger.info(f'Inventory: {current} / {total}, Remain: {current}')
            if remain == total:
                logger.hr('Triggered out of data keys')
                return True

        # Else, check other stop conditions
        return super().triggered_stop_condition()

    def run(self, name=None, folder='campaign_main', total=0):
        backup = self.config.cover(USE_DATA_KEY=True)
        super().run(name, folder, total)
        backup.recover()