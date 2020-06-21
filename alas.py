import os
import re
import time
from datetime import datetime

from module.config.config import AzurLaneConfig
from module.logger import logger, pyw_name, log_file
from module.update import Update

from module.device.device import Device


class AzurLaneAutoScript(Update):
    def __init__(self, ini_name=''):
        if not ini_name:
            ini_name = pyw_name
        ini_name = ini_name.lower()
        self.config = AzurLaneConfig(ini_name)
        self.device = None

    def run(self, command):
        self.config.start_time = datetime.now()
        try:
            self.device = Device(config=self.config)
            self.__getattribute__(command.lower())()
        except Exception as e:
            logger.exception(e)

            if self.config.ENABLE_ERROR_LOG_AND_SCREENSHOT_SAVE:
                folder = f'./log/error/{int(time.time() * 1000)}'
                logger.info(f'Saving error: {folder}')
                os.mkdir(folder)
                for data in logger.screenshot_deque:
                    image_time = datetime.strftime(data['time'], '%Y-%m-%d_%H-%M-%S-%f')
                    data['image'].save(f'{folder}/{image_time}.png')
                with open(log_file, 'r') as f:
                    start = 0
                    for index, line in enumerate(f.readlines()):
                        if re.search('\+-{15,}\+', line):
                            start = index
                with open(log_file, 'r') as f:
                    text = f.readlines()[start - 2:]
                with open(f'{folder}/log.txt', 'w') as f:
                    f.writelines(text)

    def reward_when_finished(self):
        from module.reward.reward import Reward
        az = Reward(self.config, device=self.device)
        az.reward_loop()

    def setting(self):
        for key, value in self.config.config['Setting'].items():
            print(f'{key} = {value}')

        logger.hr('Settings saved')
        # self.update_check()
        self.config.config_check()

    # def update_check(self):
    #     from module.update import Update
    #     ad = Update(self.config)
    #     if self.config.UPDATE_CHECK:
    #         ad.get_latest_commit()

    def reward(self):
        for key, value in self.config.config['Reward'].items():
            print(f'{key} = {value}')

        logger.hr('Reward Settings saved')
        self.reward_when_finished()

    def emulator(self):
        for key, value in self.config.config['Emulator'].items():
            print(f'{key} = {value}')

        logger.hr('Emulator saved')
        # self.update_check()
        from module.handler.login import LoginHandler
        az = LoginHandler(self.config, device=self.device)
        if az.app_ensure_start():
            from module.reward.reward import Reward
            az = Reward(self.config, device=self.device)
            az.reward()

    def main(self):
        """
        Method to run main chapter.
        """
        from module.campaign.run import CampaignRun
        az = CampaignRun(self.config, device=self.device)
        az.run(self.config.CAMPAIGN_NAME)
        self.reward_when_finished()

    def daily(self):
        """
        Method to run daily missions.
        """
        if self.config.ENABLE_DAILY_MISSION:
            from module.daily.daily import Daily
            az = Daily(self.config, device=self.device)
            if not az.record_executed_since():
                az.run()
                az.record_save()

        if self.config.ENABLE_HARD_CAMPAIGN:
            from module.hard.hard import CampaignHard
            az = CampaignHard(self.config, device=self.device)
            if not az.record_executed_since():
                az.run()
                az.record_save()

        if self.config.ENABLE_EXERCISE:
            from module.exercise.exercise import Exercise
            az = Exercise(self.config, device=self.device)
            if not az.record_executed_since():
                az.run()
                az.record_save()

        self.reward_when_finished()

    def event(self):
        """
        Method to run event.
        """
        from module.campaign.run import CampaignRun
        az = CampaignRun(self.config, device=self.device)
        az.run(self.config.CAMPAIGN_EVENT, folder=self.config.EVENT_NAME)
        self.reward_when_finished()

    def event_daily_ab(self):
        from module.event.campaign_ab import CampaignAB
        az = CampaignAB(self.config, device=self.device)
        az.run_event_daily()
        self.reward_when_finished()

    def semi_auto(self):
        from module.daemon.daemon import AzurLaneDaemon
        az = AzurLaneDaemon(self.config, device=self.device)
        az.daemon()

    def c72_mystery_farming(self):
        from module.campaign.run import CampaignRun
        az = CampaignRun(self.config, device=self.device)
        az.run('campaign_7_2_mystery_farming')
        self.reward_when_finished()

    def c124_leveling(self):
        from module.campaign.run import CampaignRun
        az = CampaignRun(self.config, device=self.device)
        az.run('campaign_12_4_leveling')
        self.reward_when_finished()

    def c122_leveling(self):
        from module.campaign.run import CampaignRun
        az = CampaignRun(self.config, device=self.device)
        az.run('campaign_12_2_leveling')
        self.reward_when_finished()

    def retire(self):
        from module.retire.retirement import Retirement
        az = Retirement(self.config, device=self.device)
        az.device.screenshot()
        az.retire_ships(amount=2000)


# alas = AzurLaneAutoScript()
# alas.reward()
