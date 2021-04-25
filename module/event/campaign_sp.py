import os

from module.campaign.run import CampaignRun
from module.logger import logger

RECORD_SINCE = (0,)
RECORD_OPTION = ('EventABRecord', 'sp')


class CampaignSP(CampaignRun):
    _fleet_backup: tuple

    def run_event_daily_sp(self):
        """
        Returns:
            bool: If executed.
        """
        if not os.path.exists(f'./campaign/{self.config.EVENT_NAME_AB}/sp.py'):
            logger.info('This event do not have SP, skip')
            return False

        self.reward_backup_daily_reward_settings()

        fleet_1, fleet_2 = (2, 1) if self.config.EVENT_SP_MOB_FLEET == 2 else (1, 2)
        backup = self.config.cover(FLEET_1=fleet_1, FLEET_2=fleet_2, ENABLE_FLEET_REVERSE_IN_HARD=False)

        if not self.config.record_executed_since(option=RECORD_OPTION, since=RECORD_SINCE):
            self.run(name='sp', folder=self.config.EVENT_NAME_AB, total=1)
            self.config.record_save(option=RECORD_OPTION)
            executed = True
        else:
            executed = False

        backup.recover()
        self.reward_recover_daily_reward_settings()
        return executed
