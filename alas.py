import time

import inflection
from cached_property import cached_property

from module.campaign.gems_farming import GemsFarming
from module.campaign.run import CampaignRun
from module.commission.commission import RewardCommission
from module.config.config import AzurLaneConfig, TaskEnd
from module.config.db import Database
from module.device.device import Device
from module.exception import *
from module.handler.login import LoginHandler
from module.logger import logger
from module.research.research import RewardResearch
from module.tactical.tactical_class import RewardTacticalClass
from module.ui.ui import UI, page_main


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
        while 1:
            try:
                self.__getattribute__(command)()
                UI(config=self.config, device=self.device).ui_ensure(page_main)
                return True
            except TaskEnd:
                return True
            except GameNotRunningError as e:
                logger.warning(e)
                az = LoginHandler(self.config, device=self.device)
                az.app_restart()
                az.ensure_no_unfinished_campaign()
                continue
            except GameTooManyClickError as e:
                logger.warning(e)
                self.save_error_log()
                az = LoginHandler(self.config, device=self.device)
                az.handle_game_stuck()
                continue
            except GameStuckError as e:
                logger.warning(e)
                self.save_error_log()
                az = LoginHandler(self.config, device=self.device)
                az.handle_game_stuck()
                continue
            except LogisticsRefreshBugHandler as e:
                logger.warning(e)
                self.save_error_log()
                az = LoginHandler(self.config, device=self.device)
                az.device.app_stop()
                time.sleep(600)
                az.app_ensure_start()
                continue
            except Exception as e:
                logger.exception(e)
                self.save_error_log()
                return False

    def save_error_log(self):
        """
        Save last 60 screenshots in ./log/error/<timestamp>
        Save logs to ./log/error/<timestamp>/log.txt
        """
        pass

    def research(self):
        RewardResearch(config=self.config, device=self.device).run()

    def commission(self):
        RewardCommission(config=self.config, device=self.device).run()

    def tactical(self):
        RewardTacticalClass(config=self.config, device=self.device).run()

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
            success = self.run(inflection.underscore(self.config.task))

            logger.info(f'Scheduler: End task `{self.config.task}`')
            del self.__dict__['config']

            if not success:
                break


if __name__ == '__main__':
    alas = AzurLaneAutoScript()
    alas.loop()
