from campaign.campaign_war_archives.campaign_base import CampaignBase, CampaignNameError
from module.campaign.run import CampaignRun
from module.ocr.ocr import DigitCounter
from module.war_archives.assets import OCR_DATA_KEY_CAMPAIGN
from module.logger import logger

DATA_KEY_CAMPAIGN = DigitCounter(OCR_DATA_KEY_CAMPAIGN, letter=(255, 247, 247), threshold=64)

class CampaignWarArchives(CampaignRun, CampaignBase):
    def triggered_stop_condition(self):
        # In case already inside campaign, OCR cannot be read otherwise
        if self._in_archives_campaign():
            # Check for 0 data keys left to use
            current, remain, total = DATA_KEY_CAMPAIGN.ocr(self.device.image)
            logger.info(f'Inventory: {current} / {total}, Remain: {current}')
            if remain == total:
                logger.hr('Triggered out of data keys')
                return True

        # Else, check other stop conditions
        return super().triggered_stop_condition()