import os
import re
import time
from datetime import datetime

import inflection
from cached_property import cached_property

from module.campaign.gems_farming import GemsFarming
from module.campaign.run import CampaignRun
from module.commission.commission import RewardCommission
from module.config.config import AzurLaneConfig, TaskEnd
from module.config.db import Database
from module.daily.daily import Daily
from module.device.device import Device
from module.dorm.dorm import RewardDorm
from module.exception import *
from module.guild.guild_reward import RewardGuild
from module.handler.login import LoginHandler
from module.handler.sensitive_info import handle_sensitive_image, handle_sensitive_logs
from module.hard.hard import CampaignHard
from module.logger import logger, log_file
from module.meowfficer.meowfficer import RewardMeowfficer
from module.research.research import RewardResearch
from module.reward.reward import Reward
from module.tactical.tactical_class import RewardTacticalClass


class AzurLaneAutoScript:
    def __init__(self, config_name='alas'):
        self.config_name = config_name
        Database().update_config(config_name)

    @cached_property
    def config(self):
        config = AzurLaneConfig(config_name=self.config_name)
        return config

    @cached_property
    def device(self):
        device = Device(config=self.config)
        return device

    def run(self, command):
        try:
            self.__getattribute__(command)()
            return True
        except TaskEnd:
            return True
        except GameNotRunningError as e:
            logger.warning(e)
            self.config.task_call('Restart')
            return True
        except (GameStuckError, GameTooManyClickError) as e:
            logger.warning(e)
            self.save_error_log()
            logger.warning(f'Game stuck, {self.config.Emulator_PackageName} will be restarted in 10 seconds')
            logger.warning('If you are playing by hand, please stop Alas')
            self.config.task_call('Restart')
            self.device.sleep(10)
            return False
        except LogisticsRefreshBugHandler as e:
            logger.warning(e)
            self.save_error_log()
            self.config.task_call('Restart')
            self.device.sleep(10)
            return False
        except ScriptError as e:
            logger.critical(e)
            logger.critical('This is likely to be a mistake of developers, but sometimes just random issues')
            exit(1)
        except RequestHumanTakeover:
            logger.critical('Request human takeover')
            exit(1)
        except Exception as e:
            logger.exception(e)
            self.save_error_log()
            exit(1)

    def save_error_log(self):
        """
        Save last 60 screenshots in ./log/error/<timestamp>
        Save logs to ./log/error/<timestamp>/log.txt
        """
        if self.config.Error_SaveError:
            folder = f'./log/error/{int(time.time() * 1000)}'
            logger.warning(f'Saving error: {folder}')
            os.mkdir(folder)
            for data in self.device.screenshot_deque:
                image_time = datetime.strftime(data['time'], '%Y-%m-%d_%H-%M-%S-%f')
                image = handle_sensitive_image(data['image'])
                image.save(f'{folder}/{image_time}.png')
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                start = 0
                for index, line in enumerate(lines):
                    if re.search('\+-{15,}\+', line):
                        start = index
                lines = lines[start - 2:]
                lines = handle_sensitive_logs(lines)
            with open(f'{folder}/log.txt', 'w', encoding='utf-8') as f:
                f.writelines(lines)

    def restart(self):
        LoginHandler(self.config, device=self.device).app_restart()

    def research(self):
        RewardResearch(config=self.config, device=self.device).run()

    def commission(self):
        RewardCommission(config=self.config, device=self.device).run()

    def tactical(self):
        RewardTacticalClass(config=self.config, device=self.device).run()

    def dorm(self):
        RewardDorm(config=self.config, device=self.device).run()

    def guild(self):
        RewardGuild(config=self.config, device=self.device).run()

    def reward(self):
        Reward(config=self.config, device=self.device).run()

    def meowfficer(self):
        RewardMeowfficer(config=self.config, device=self.device).run()

    def daily(self):
        Daily(config=self.config, device=self.device).run()

    def hard(self):
        CampaignHard(config=self.config, device=self.device).run()

    def main(self):
        CampaignRun(config=self.config, device=self.device).run(
            name=self.config.Campaign_Name,
            folder=self.config.Campaign_Event,
            mode=self.config.Campaign_Mode)

    def gems_farming(self):
        GemsFarming(config=self.config, device=self.device).run(
            name=self.config.Campaign_Name,
            folder=self.config.Campaign_Event,
            mode=self.config.Campaign_Mode)

    def loop(self):
        while 1:
            logger.info(f'Scheduler: Start task `{self.config.task}`')
            logger.hr(self.config.task, level=0)
            success = self.run(inflection.underscore(self.config.task))

            logger.info(f'Scheduler: End task `{self.config.task}`')

            if success:
                del self.__dict__['config']
                continue
            elif self.config.Error_HandleError:
                # self.config.task_delay(success=False)
                del self.__dict__['config']
                continue
            else:
                break


if __name__ == '__main__':
    alas = AzurLaneAutoScript()
    alas.loop()
