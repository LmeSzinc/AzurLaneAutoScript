from module.config.config import AzurLaneConfig
from module.logger import logger, pyw_name


class AzurLaneAutoScript:
    def __init__(self, ini_name=''):
        if not ini_name:
            ini_name = pyw_name
        ini_name = ini_name.lower()
        self.config = AzurLaneConfig(ini_name)

    def setting(self):
        for key, value in self.config.config['Setting'].items():
            print(f'{key} = {value}')

        logger.hr('Settings saved')

    def reward(self):
        for key, value in self.config.config['Reward'].items():
            print(f'{key} = {value}')

        logger.hr('Reward Settings saved')

    def emulator(self):
        for key, value in self.config.config['Emulator'].items():
            print(f'{key} = {value}')

        logger.hr('Emulator saved')
        from module.handler.login import LoginHandler
        az = LoginHandler(self.config)
        az.app_ensure_start()

    def main(self):
        """
        Method to run main chapter.
        """
        from module.campaign.run import CampaignRun
        az = CampaignRun(self.config)
        az.run(self.config.CAMPAIGN_NAME)

    def daily(self):
        """
        Method to run daily missions.
        """
        if self.config.ENABLE_DAILY_MISSION:
            from module.daily.daily import Daily
            az = Daily(self.config)
            if not az.record_executed_since():
                az.run()
                az.record_save()

        if self.config.ENABLE_HARD_CAMPAIGN:
            from module.hard.hard import CampaignHard
            az = CampaignHard(self.config)
            if not az.record_executed_since():
                az.run()
                az.record_save()

        if self.config.ENABLE_EXERCISE:
            from module.exercise.exercise import Exercise
            az = Exercise(self.config)
            if not az.record_executed_since():
                az.run()
                az.record_save()

    def event(self):
        """
        Method to run event.
        """
        from module.campaign.run import CampaignRun
        az = CampaignRun(self.config)
        az.run(self.config.CAMPAIGN_EVENT, folder=self.config.EVENT_NAME)

    def event_daily_ab(self):
        from module.event.campaign_ab import CampaignAB
        az = CampaignAB(self.config)
        az.run_event_daily()

    def semi_auto(self):
        from module.daemon.daemon import AzurLaneDaemon
        az = AzurLaneDaemon(self.config)
        az.daemon()

    def c72_mystery_farming(self):
        from module.campaign.run import CampaignRun
        az = CampaignRun(self.config)
        az.run('campaign_7_2_mystery_farming')

    def c124_leveling(self):
        from module.campaign.run import CampaignRun
        az = CampaignRun(self.config)
        az.run('campaign_12_4_leveling')

    def retire(self):
        from module.retire.retirement import Retirement
        az = Retirement(self.config)
        az.retire_ships(amount=2000)


# alas = AzurLaneAutoScript()
# alas.reward()
