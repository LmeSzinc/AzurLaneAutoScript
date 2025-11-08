import re

from campaign.campaign_war_archives.campaign_base import CampaignBase
from module.campaign.run import CampaignRun
from module.logger import logger
from module.ocr.ocr import DigitCounter
from module.war_archives.assets import (OCR_DATA_KEY_CAMPAIGN,
                                        WAR_ARCHIVES_CAMPAIGN_CHECK)


class OcrDataKey(DigitCounter):
    def after_process(self, result):
        result = super().after_process(result)
        result = re.sub(r'(\d{1,2})60$', r'\1/60', result)
        return result


DATA_KEY_CAMPAIGN = OcrDataKey(OCR_DATA_KEY_CAMPAIGN, letter=(255, 247, 247), threshold=64)


class CampaignWarArchives(CampaignRun, CampaignBase):
    def triggered_stop_condition(self, oil_check=True):
        # Must be in archives campaign to OCR check
        if self.appear(WAR_ARCHIVES_CAMPAIGN_CHECK, offset=(20, 20)):
            # Check for 0 data keys left to use
            current, remain, total = DATA_KEY_CAMPAIGN.ocr(self.device.image)
            logger.info(f'Inventory: {current} / {total}, Remain: {current}')
            if remain == total:
                logger.hr('Triggered out of data keys')
                # Only triggered out of data keys can it delay the task
                self.config.task_delay(server_update=True)
                return True

        # Else, check other stop conditions
        return super().triggered_stop_condition(oil_check)

    def can_use_auto_search_continue(self):
        """
        Auto search menu has blur background and covers DATA_KEY_CAMPAIGN, close it.
        """
        return False

    def run(self, name=None, folder='campaign_main', mode='normal', total=0):
        self.config.override(USE_DATA_KEY=True)
        super().run(name, folder, mode, total)
