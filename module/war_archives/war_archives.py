from campaign.campaign_war_archives.campaign_base import CampaignBase
from module.campaign.run import CampaignRun
from module.logger import logger
from module.ocr.ocr import DigitCounter
from module.war_archives.assets import OCR_DATA_KEY_CAMPAIGN, WAR_ARCHIVES_CAMPAIGN_CHECK

DATA_KEY_CAMPAIGN = DigitCounter(OCR_DATA_KEY_CAMPAIGN, letter=(255, 247, 247), threshold=64)
RECORD_SINCE = (0,)
RECORD_OPTION = ('DailyRecord', 'war_archives')

class CampaignWarArchives(CampaignRun, CampaignBase):
    def triggered_stop_condition(self, oil_check=True):
        # Must be in archives campaign to OCR check
        if self.appear(WAR_ARCHIVES_CAMPAIGN_CHECK, offset=(20, 20)):
            # Check for 0 data keys left to use
            current, remain, total = DATA_KEY_CAMPAIGN.ocr(self.device.image)
            logger.info(f'Inventory: {current} / {total}, Remain: {current}')
            if remain == total:
                logger.hr('Triggered out of data keys')
                return True

        # Else, check other stop conditions
        return super().triggered_stop_condition(oil_check)

    def run_war_archives_daily(self):
        """
        Returns:
            bool: If executed.
        """
        self.reward_backup_daily_reward_settings()
        backup = self.config.cover(STOP_IF_COUNT_GREATER_THAN=4)  # 4 data keys daily
        if not self.config.record_executed_since(option=RECORD_OPTION, since=RECORD_SINCE):
            self.run(self.config.WAR_ARCHIVES_STAGE, folder=self.config.WAR_ARCHIVES_NAME)
            self.config.record_save(option=RECORD_OPTION)
            executed = True
        else:
            executed = False

        backup.recover()
        self.reward_recover_daily_reward_settings()
        return executed

    def run(self, name=None, folder='campaign_main', total=0):
        backup = self.config.cover(USE_DATA_KEY=True)
        super().run(name, folder, total)
        backup.recover()
