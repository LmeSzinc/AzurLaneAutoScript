import os
import re
import threading
import time
from datetime import datetime

import inflection
from cached_property import cached_property

from module.config.config import AzurLaneConfig, TaskEnd
from module.config.config_updater import ConfigUpdater
from module.config.utils import deep_get, deep_set
from module.exception import *
from module.logger import logger


class AzurLaneAutoScript:
    stop_event: threading.Event = None

    def __init__(self, config_name='alas'):
        logger.hr('Start', level=0)
        self.config_name = config_name
        ConfigUpdater().update_file(config_name)

    @cached_property
    def config(self):
        try:
            config = AzurLaneConfig(config_name=self.config_name)
            return config
        except RequestHumanTakeover:
            logger.critical('Request human takeover')
            exit(1)
        except Exception as e:
            logger.exception(e)
            exit(1)

    @cached_property
    def device(self):
        try:
            from module.device.device import Device
            device = Device(config=self.config)
            return device
        except RequestHumanTakeover:
            logger.critical('Request human takeover')
            exit(1)
        except Exception as e:
            logger.exception(e)
            exit(1)

    def run(self, command):
        try:
            self.device.screenshot()
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
            logger.warning(f'Game stuck, {self.device.package} will be restarted in 10 seconds')
            logger.warning('If you are playing by hand, please stop Alas')
            self.config.task_call('Restart')
            self.device.sleep(10)
            return False
        except GameBugError as e:
            logger.warning(e)
            self.save_error_log()
            logger.warning('An error has occurred in Azur Lane game client, Alas is unable to handle')
            logger.warning(f'Restarting {self.device.package} to fix it')
            self.config.task_call('Restart')
            self.device.sleep(10)
            return False
        except GamePageUnknownError:
            logger.critical('Game page unknown')
            self.save_error_log()
            exit(1)
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
        from module.base.utils import save_image
        from module.handler.sensitive_info import (handle_sensitive_image,
                                                   handle_sensitive_logs)
        if self.config.Error_SaveError:
            if not os.path.exists('./log/error'):
                os.mkdir('./log/error')
            folder = f'./log/error/{int(time.time() * 1000)}'
            logger.warning(f'Saving error: {folder}')
            os.mkdir(folder)
            for data in self.device.screenshot_deque:
                image_time = datetime.strftime(data['time'], '%Y-%m-%d_%H-%M-%S-%f')
                image = handle_sensitive_image(data['image'])
                save_image(image, f'{folder}/{image_time}.png')
            with open(logger.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                start = 0
                for index, line in enumerate(lines):
                    line = line.strip(' \r\t\n')
                    if re.match('^═{15,}$', line):
                        start = index
                lines = lines[start - 2:]
                lines = handle_sensitive_logs(lines)
            with open(f'{folder}/log.txt', 'w', encoding='utf-8') as f:
                f.writelines(lines)

    def restart(self):
        from module.handler.login import LoginHandler
        LoginHandler(self.config, device=self.device).app_restart()

    def start(self):
        from module.handler.login import LoginHandler
        LoginHandler(self.config, device=self.device).app_start()

    def goto_main(self):
        from module.handler.login import LoginHandler
        from module.ui.ui import UI
        if self.device.app_is_running():
            logger.info('App is already running, goto main page')
            UI(self.config, device=self.device).ui_goto_main()
        else:
            logger.info('App is not running, start app and goto main page')
            LoginHandler(self.config, device=self.device).app_start()
            UI(self.config, device=self.device).ui_goto_main()

    def research(self):
        from module.research.research import RewardResearch
        RewardResearch(config=self.config, device=self.device).run()

    def commission(self):
        from module.commission.commission import RewardCommission
        RewardCommission(config=self.config, device=self.device).run()

    def tactical(self):
        from module.tactical.tactical_class import RewardTacticalClass
        RewardTacticalClass(config=self.config, device=self.device).run()

    def dorm(self):
        from module.dorm.dorm import RewardDorm
        RewardDorm(config=self.config, device=self.device).run()

    def meowfficer(self):
        from module.meowfficer.meowfficer import RewardMeowfficer
        RewardMeowfficer(config=self.config, device=self.device).run()

    def guild(self):
        from module.guild.guild_reward import RewardGuild
        RewardGuild(config=self.config, device=self.device).run()

    def reward(self):
        from module.reward.reward import Reward
        Reward(config=self.config, device=self.device).run()

    def shop_frequent(self):
        from module.shop.shop_reward import RewardShop
        RewardShop(config=self.config, device=self.device).run_frequent()

    def shop_once(self):
        from module.shop.shop_reward import RewardShop
        RewardShop(config=self.config, device=self.device).run_once()

    def shipyard(self):
        from module.shipyard.shipyard_reward import RewardShipyard
        RewardShipyard(config=self.config, device=self.device).run()

    def gacha(self):
        from module.gacha.gacha_reward import RewardGacha
        RewardGacha(config=self.config, device=self.device).run()

    def data_key(self):
        from module.data_key.data_key import RewardDataKey
        RewardDataKey(config=self.config, device=self.device).run()

    def supply_pack(self):
        from module.supply_pack.supply_pack import SupplyPack
        SupplyPack(config=self.config, device=self.device).run()

    def battle_pass(self):
        from module.battle_pass.battle_pass import BattlePass
        BattlePass(config=self.config, device=self.device).run()

    def meta_reward(self):
        from module.meta_reward.meta_reward import MetaReward
        MetaReward(config=self.config, device=self.device).run()

    def daily(self):
        from module.daily.daily import Daily
        Daily(config=self.config, device=self.device).run()

    def hard(self):
        from module.hard.hard import CampaignHard
        CampaignHard(config=self.config, device=self.device).run()

    def exercise(self):
        from module.exercise.exercise import Exercise
        Exercise(config=self.config, device=self.device).run()

    def sos(self):
        from module.sos.sos import CampaignSos
        CampaignSos(config=self.config, device=self.device).run()

    def war_archives(self):
        from module.war_archives.war_archives import CampaignWarArchives
        CampaignWarArchives(config=self.config, device=self.device).run(
            name=self.config.Campaign_Name, folder=self.config.Campaign_Event, mode=self.config.Campaign_Mode)

    def raid_daily(self):
        from module.raid.daily import RaidDaily
        RaidDaily(config=self.config, device=self.device).run()

    def event_ab(self):
        from module.event.campaign_ab import CampaignAB
        CampaignAB(config=self.config, device=self.device).run()

    def event_cd(self):
        from module.event.campaign_cd import CampaignCD
        CampaignCD(config=self.config, device=self.device).run()

    def event_sp(self):
        from module.event.campaign_sp import CampaignSP
        CampaignSP(config=self.config, device=self.device).run()

    def maritime_escort(self):
        from module.event.maritime_escort import MaritimeEscort
        MaritimeEscort(config=self.config, device=self.device).run()

    def opsi_ash_assist(self):
        from module.os_ash.ash import AshBeaconAssist
        AshBeaconAssist(config=self.config, device=self.device).run()

    def opsi_explore(self):
        from module.campaign.os_run import OSCampaignRun
        OSCampaignRun(config=self.config, device=self.device).opsi_explore()

    def opsi_shop(self):
        from module.campaign.os_run import OSCampaignRun
        OSCampaignRun(config=self.config, device=self.device).opsi_shop()

    def opsi_daily(self):
        from module.campaign.os_run import OSCampaignRun
        OSCampaignRun(config=self.config, device=self.device).opsi_daily()

    def opsi_obscure(self):
        from module.campaign.os_run import OSCampaignRun
        OSCampaignRun(config=self.config, device=self.device).opsi_obscure()

    def opsi_abyssal(self):
        from module.campaign.os_run import OSCampaignRun
        OSCampaignRun(config=self.config, device=self.device).opsi_abyssal()

    def opsi_stronghold(self):
        from module.campaign.os_run import OSCampaignRun
        OSCampaignRun(config=self.config, device=self.device).opsi_stronghold()

    def opsi_meowfficer_farming(self):
        from module.campaign.os_run import OSCampaignRun
        OSCampaignRun(config=self.config, device=self.device).opsi_meowfficer_farming()

    def main(self):
        from module.campaign.run import CampaignRun
        CampaignRun(config=self.config, device=self.device).run(
            name=self.config.Campaign_Name, folder=self.config.Campaign_Event, mode=self.config.Campaign_Mode)

    def main2(self):
        from module.campaign.run import CampaignRun
        CampaignRun(config=self.config, device=self.device).run(
            name=self.config.Campaign_Name, folder=self.config.Campaign_Event, mode=self.config.Campaign_Mode)

    def main3(self):
        from module.campaign.run import CampaignRun
        CampaignRun(config=self.config, device=self.device).run(
            name=self.config.Campaign_Name, folder=self.config.Campaign_Event, mode=self.config.Campaign_Mode)

    def event(self):
        from module.campaign.run import CampaignRun
        CampaignRun(config=self.config, device=self.device).run(
            name=self.config.Campaign_Name, folder=self.config.Campaign_Event, mode=self.config.Campaign_Mode)

    def event2(self):
        from module.campaign.run import CampaignRun
        CampaignRun(config=self.config, device=self.device).run(
            name=self.config.Campaign_Name, folder=self.config.Campaign_Event, mode=self.config.Campaign_Mode)

    def raid(self):
        from module.raid.run import RaidRun
        RaidRun(config=self.config, device=self.device).run()

    def c72_mystery_farming(self):
        from module.campaign.run import CampaignRun
        CampaignRun(config=self.config, device=self.device).run(
            name=self.config.Campaign_Name, folder=self.config.Campaign_Event, mode=self.config.Campaign_Mode)

    def c122_medium_leveling(self):
        from module.campaign.run import CampaignRun
        CampaignRun(config=self.config, device=self.device).run(
            name=self.config.Campaign_Name, folder=self.config.Campaign_Event, mode=self.config.Campaign_Mode)

    def c124_large_leveling(self):
        from module.campaign.run import CampaignRun
        CampaignRun(config=self.config, device=self.device).run(
            name=self.config.Campaign_Name, folder=self.config.Campaign_Event, mode=self.config.Campaign_Mode)

    def gems_farming(self):
        from module.campaign.gems_farming import GemsFarming
        GemsFarming(config=self.config, device=self.device).run(
            name=self.config.Campaign_Name, folder=self.config.Campaign_Event, mode=self.config.Campaign_Mode)

    def wait_until(self, future):
        """
        Wait until a specific time.

        Args:
            future (datetime):
        """
        seconds = future.timestamp() - datetime.now().timestamp() + 1
        if seconds <= 0:
            logger.warning(f'Wait until {str(future)}, but sleep length < 0, skip waiting')
            return

        if self.stop_event is not None:
            self.stop_event.wait(seconds)
            if self.stop_event.is_set():
                logger.info("Update event detected")
                logger.info(f"[{self.config_name}] exited. Reason: Update")
                exit(0)
        else:
            time.sleep(seconds)

    def get_next_task(self):
        """
        Returns:
            str: Name of the next task.
        """

        task = self.config.get_next()
        self.config.task = task
        self.config.bind(task)

        from module.base.resource import release_resources
        if self.config.task.command != 'Alas':
            release_resources(next_task=task.command)

        if task.next_run > datetime.now():
            logger.info(f'Wait until {task.next_run} for task `{task.command}`')
            method = self.config.Optimization_WhenTaskQueueEmpty
            if method == 'close_game':
                logger.info('Close game during wait')
                self.device.app_stop()
                release_resources()
                self.wait_until(task.next_run)
                self.run('start')
            elif method == 'goto_main':
                logger.info('Goto main page during wait')
                self.run('goto_main')
                release_resources()
                self.wait_until(task.next_run)
            elif method == 'stay_there':
                logger.info('Stay there during wait')
                release_resources()
                self.wait_until(task.next_run)
            else:
                logger.warning(f'Invalid Optimization_WhenTaskQueueEmpty: {method}, fallback to stay_there')
                release_resources()
                self.wait_until(task.next_run)

        AzurLaneConfig.is_hoarding_task = False
        return task.command

    def loop(self):
        logger.set_file_logger(self.config_name)
        logger.info(f'Start scheduler loop: {self.config_name}')
        is_first = True
        failure_record = {}

        while 1:
            if self.stop_event is not None:
                if self.stop_event.is_set():
                    logger.info("Update event detected")
                    logger.info(f"Alas [{self.config_name}] exited.")
                    break
            task = self.get_next_task()

            # Skip first restart
            if is_first and task == 'Restart':
                logger.info('Skip task `Restart` at scheduler start')
                self.config.task_delay(server_update=True)
                del self.__dict__['config']
                continue

            # Run
            logger.info(f'Scheduler: Start task `{task}`')
            self.device.stuck_record_clear()
            self.device.click_record_clear()
            logger.hr(task, level=0)
            success = self.run(inflection.underscore(task))
            logger.info(f'Scheduler: End task `{task}`')
            is_first = False

            # Check failures
            failed = deep_get(failure_record, keys=task, default=0)
            failed = 0 if success else failed + 1
            deep_set(failure_record, keys=task, value=failed)
            if failed >= 3:
                logger.critical(f"Task `{task}` failed 3 or more times.")
                logger.critical("Possible reason #1: You haven't used it correctly. "
                                "Please read the help text of the options.")
                logger.critical("Possible reason #2: There is a problem with this task. "
                                "Please contact developers or try to fix it yourself.")
                logger.critical('Request human takeover')
                exit(1)

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
