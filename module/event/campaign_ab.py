import os

from module.campaign.run import CampaignRun
from module.logger import logger

RECORD_SINCE = (0,)
CAMPAIGN_NAME = ['a1', 'a2', 'a3', 'a4', 'b1', 'b2', 'b3', 'b4', 'c1', 'c2', 'c3', 'c4', 'd1', 'd2', 'd3', 'd4']


class CampaignAB(CampaignRun):
    def run(self, name, folder='campaign_main', total=0):
        """
        Args:
            name:
            folder:
            total:

        Returns:
            bool: If executed.
        """
        name = name.lower()
        option = ('EventABRecord', name)
        if not self.config.record_executed_since(option=option, since=RECORD_SINCE):
            super().run(name=name, folder=folder, total=1)
            self.config.record_save(option=option)
            return True
        else:
            return False

    def run_event_daily(self):
        """
        Returns:
            bool: If executed.
        """
        count = 0
        existing = [file[:-3] for file in os.listdir(f'./campaign/{self.config.EVENT_NAME_AB}') if file[-3:] == '.py']
        chapter = self.config.EVENT_AB_CHAPTER.split('_')[1]
        self.reward_backup_daily_reward_settings()

        for name in existing:
            if name.lower().startswith('sp'):
                logger.warning(f'{self.config.EVENT_NAME_AB} seems to be a SP event, skip daily_ab')
                logger.warning(f'Existing map files: {existing}')
                return False

        for name in CAMPAIGN_NAME:
            if name not in existing:
                continue
            if name[0] not in chapter:
                continue
            result = self.run(name=name, folder=self.config.EVENT_NAME_AB)
            if result:
                count += 1

        self.reward_recover_daily_reward_settings()
        logger.info(f'Event daily ab executed: {count}')
        return count > 0
