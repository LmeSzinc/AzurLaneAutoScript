# rev: auto_restart
# 基于原版 alas.py 增加了自动尝试重启调度器的功能
# 用于解决 Unknown ui page 、短暂网络不良等 无需人工修复的偶发意外情形，避免调度器直接终止
# Modified: run, loop
# Last Updated: 2025-09-01 00:03
import os
import re
import shutil
import threading
import time
from datetime import datetime, timedelta

import inflection
from cached_property import cached_property

from module.base.decorator import del_cached_property
from module.base.api_client import ApiClient
from module.config.config import AzurLaneConfig, TaskEnd
from module.config.deep import deep_get, deep_set
from module.exception import *
from module.logger import logger
from module.notify import handle_notify


RESTART_SENSITIVE_TASKS = ['Commission', 'Research']


class AzurLaneAutoScript:
    stop_event: threading.Event = None

    def __init__(self, config_name='alas'):
        logger.hr('Start', level=0)
        self.config_name = config_name
        # Skip first restart
        self.is_first_task = True
        # Failure count of tasks
        # Key: str, task name, value: int, failure count
        self.failure_record = {}
        # Restart counters
        self.consecutive_game_stuck = 0
        self.consecutive_adb_offline = 0
        # Scheduled emulator restart
        self.last_emulator_restart_time = time.time()

    def _try_restart_emulator(self):
        """
        Try to restart the emulator if AdbOfflineRestart is enabled and threshold not reached.
        
        Uses the existing self.device object if available, as it has emulator_instance cached.
        If not available, falls back to a fresh PlatformWindows (Windows) or PlatformMac (macOS) instance.
        
        Returns:
            bool: True if emulator was restarted, False if restart not possible.
        """
        import sys
        
        if not self.config.Error_AdbOfflineRestart:
            logger.warning('AdbOfflineRestart is disabled, cannot auto-restart emulator')
            return False
        
        self.consecutive_adb_offline += 1
        limit = int(self.config.Error_AdbOfflineThreshold)
        logger.warning(f'EmulatorNotRunningError: consecutive count {self.consecutive_adb_offline}/{limit}')
        
        if self.consecutive_adb_offline > limit:
            logger.critical(f'EmulatorNotRunningError: Restart limit ({limit}) reached')
            return False
        
        logger.hr('Restarting Emulator', level=1)
        try:
            # Try to get existing device object
            device = self.__dict__.get('device', None)
            if device is None:
                # Fallback: create a PlatformWindows or PlatformMac object based on OS
                # Note: This might still trigger some detection but is the best fallback if device is missing
                if sys.platform == 'darwin':
                    from module.device.platform.platform_mac import PlatformMac
                    device = PlatformMac(self.config)
                else:
                    from module.device.platform.platform_windows import PlatformWindows
                    device = PlatformWindows(self.config)
            
            logger.info('Stopping emulator...')
            device.emulator_stop()
            time.sleep(5)
            logger.info('Starting emulator...')
            device.emulator_start()
            logger.info('Emulator restart complete')
            
            # Clear cached device so next access creates a fresh connection
            if 'device' in self.__dict__:
                del_cached_property(self, 'device')
            return True
        except Exception as e:
            logger.error(f'Failed to restart emulator: {e}')
            return False

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
        except EmulatorNotRunningError:
            logger.critical('Emulator is not running during device initialization')
            logger.critical('Please start the emulator and try again')
            exit(1)
        except RequestHumanTakeover:
            logger.critical('Request human takeover')
            exit(1)
        except Exception as e:
            logger.exception(e)
            exit(1)

    @cached_property
    def checker(self):
        try:
            from module.server_checker import ServerChecker
            checker = ServerChecker(server=self.config.Emulator_ServerName)
            return checker
        except Exception as e:
            logger.exception(e)
            exit(1)

    # def run(self, command, skip_first_screenshot=False):
    #     try:
    #         if not skip_first_screenshot:
    #             self.device.screenshot()
    #         self.__getattribute__(command)()
    #         return True
    #     except TaskEnd:
    #         return True
    #     except GameNotRunningError as e:
    #         logger.warning(e)
    #         self.config.task_call('Restart')
    #         return False
    #     except (GameStuckError, GameTooManyClickError) as e:
    #         logger.error(e)
    #         self.save_error_log()
    #         logger.warning(f'Game stuck, {self.device.package} will be restarted in 10 seconds')
    #         logger.warning('If you are playing by hand, please stop Alas')
    #         self.config.task_call('Restart')
    #         self.device.sleep(10)
    #         return False
    #     except GameBugError as e:
    #         logger.warning(e)
    #         self.save_error_log()
    #         logger.warning('An error has occurred in Azur Lane game client, Alas is unable to handle')
    #         logger.warning(f'Restarting {self.device.package} to fix it')
    #         self.config.task_call('Restart')
    #         self.device.sleep(10)
    #         return False
    #     except GamePageUnknownError:
    #         logger.info('Game server may be under maintenance or network may be broken, check server status now')
    #         self.checker.check_now()
    #         if self.checker.is_available():
    #             logger.critical('Game page unknown')
    #             self.save_error_log()
    #             handle_notify(
    #                 self.config.Error_OnePushConfig,
    #                 title=f"Alas <{self.config_name}> crashed",
    #                 content=f"<{self.config_name}> GamePageUnknownError",
    #             )
    #             exit(1)
    #         else:
    #             self.checker.wait_until_available()
    #             return False
    #     except ScriptError as e:
    #         logger.exception(e)
    #         logger.critical('This is likely to be a mistake of developers, but sometimes just random issues')
    #         handle_notify(
    #             self.config.Error_OnePushConfig,
    #             title=f"Alas <{self.config_name}> crashed",
    #             content=f"<{self.config_name}> ScriptError",
    #         )
    #         exit(1)
    #     except RequestHumanTakeover:
    #         logger.critical('Request human takeover')
    #         handle_notify(
    #             self.config.Error_OnePushConfig,
    #             title=f"Alas <{self.config_name}> crashed",
    #             content=f"<{self.config_name}> RequestHumanTakeover",
    #         )
    #         exit(1)
    #     except Exception as e:
    #         logger.exception(e)
    #         self.save_error_log()
    #         handle_notify(
    #             self.config.Error_OnePushConfig,
    #             title=f"Alas <{self.config_name}> crashed",
    #             content=f"<{self.config_name}> Exception occured",
    #         )
    #         exit(1)

    def run(self, command, skip_first_screenshot=False):
        """
        Run a task command.
        
        Returns:
            True: Task completed successfully
            False: Task failed with unrecoverable error (counts toward failure limit)
            'recoverable': Task failed with recoverable error (does NOT count toward failure limit)
        """
        try:
            if not skip_first_screenshot:
                self.device.screenshot()
            self.__getattribute__(command)()
            return True
        except TaskEnd:
            return True
        except GameNotRunningError as e:
            # 可恢复错误：游戏未运行，重启即可
            logger.warning(e)
            handle_notify(
                self.config.Error_OnePushConfig,
                title=f"Alas <{self.config_name}> 警告",
                content=f"<{self.config_name}> 游戏未运行 - 将自动重启游戏",
            )
            self.config.task_call('Restart')
            return 'recoverable'
        except (GameStuckError, GameTooManyClickError) as e:
            # 可恢复错误：游戏卡住或点击过多，重启即可
            logger.error(e)
            self.save_error_log()

            if self.config.Error_GameStuckRestart:
                self.consecutive_game_stuck += 1
                limit = int(self.config.Error_GameStuckThreshold)
                logger.warning(f'GameStuckError: {self.consecutive_game_stuck}/{limit}')
                if self.consecutive_game_stuck >= limit:
                    logger.warning('Game stuck too many times, restarting emulator...')
                    if self._try_restart_emulator():
                        self.consecutive_game_stuck = 0
                        self.config.task_call('Restart')
                        return 'recoverable'

            logger.warning(f'Game stuck, {self.device.package} will be restarted in 10 seconds')
            logger.warning('If you are playing by hand, please stop Alas')
            handle_notify(
                self.config.Error_OnePushConfig,
                title=f"Alas <{self.config_name}> 警告",
                content=f"<{self.config_name}> 游戏卡住 - 将自动重启游戏",
            )
            self.config.task_call('Restart')
            self.device.sleep(10)
            return 'recoverable'
        except GameBugError as e:
            # 可恢复错误：游戏客户端 bug，重启即可
            logger.warning(e)
            self.save_error_log()
            logger.warning('An error has occurred in Azur Lane game client, Alas is unable to handle')
            logger.warning(f'Restarting {self.device.package} to fix it')
            handle_notify(
                self.config.Error_OnePushConfig,
                title=f"Alas <{self.config_name}> 警告",
                content=f"<{self.config_name}> 游戏客户端错误 - 将自动重启游戏",
            )
            self.config.task_call('Restart')
            self.device.sleep(10)
            return 'recoverable'
        except GamePageUnknownError:
            logger.info('Game server may be under maintenance or network may be broken, check server status now')
            self.checker.check_now()
            if self.checker.is_available():
                logger.critical('Game page unknown')
                self.save_error_log()
                handle_notify(
                    self.config.Error_OnePushConfig,
                    title=f"Alas <{self.config_name}> crashed",
                    content=f"<{self.config_name}> GamePageUnknownError",
                )
                exit(1)
            else:
                self.checker.wait_until_available()
                return False
        except ScriptError as e:
            logger.exception(e)
            logger.critical('This is likely to be a mistake of developers, but sometimes just random issues')
            handle_notify(
                self.config.Error_OnePushConfig,
                title=f"Alas <{self.config_name}> crashed",
                content=f"<{self.config_name}> ScriptError",
            )
            # exit(1)
            raise
        except EmulatorNotRunningError:
            # 模拟器离线/死机，尝试自动重启模拟器
            logger.error('EmulatorNotRunningError during task execution')
            self.save_error_log()
            if self._try_restart_emulator():
                # 重启成功，调度 Restart 任务重新启动游戏
                self.config.task_call('Restart')
                handle_notify(
                    self.config.Error_OnePushConfig,
                    title=f"Alas <{self.config_name}> 警告",
                    content=f"<{self.config_name}> 模拟器离线 - 已自动重启模拟器",
                )
                return 'recoverable'
            else:
                # 重启失败或未启用，终止程序
                logger.critical('Emulator not running and auto-restart failed or disabled')
                handle_notify(
                    self.config.Error_OnePushConfig,
                    title=f"Alas <{self.config_name}> crashed",
                    content=f"<{self.config_name}> EmulatorNotRunningError",
                )
                exit(1)
        except RequestHumanTakeover:
            logger.critical('Request human takeover')
            handle_notify(
                self.config.Error_OnePushConfig,
                title=f"Alas <{self.config_name}> crashed",
                content=f"<{self.config_name}> RequestHumanTakeover",
            )
            exit(1)
        except AutoSearchSetError:
            logger.critical('Auto search could not be set correctly. Maybe your ships in hard mode are changed.')
            logger.critical('Request human takeover.')
            exit(1)
        except Exception as e:
            logger.exception(e)
            self.save_error_log()
            handle_notify(
                self.config.Error_OnePushConfig,
                title=f"Alas <{self.config_name}> crashed",
                content=f"<{self.config_name}> Exception occured",
            )
            # exit(1)
            raise

    def keep_last_errlog(self, folder_path, n: int = 30):
        """

        Keep last n folders in folder_path, delete others.
        If n is negative or 0, do nothing.(Keep all errlog folders)

        Args:
            folder_path (str): Path to folder.\n
            n (int): Number of folders to keep.
        """
        if n <= 0:
            return
        folders = [
            os.path.join(folder_path, f)
            for f in os.listdir(folder_path)
            if os.path.isdir(os.path.join(folder_path, f))
        ]
        for folder in folders[:-n]:
            shutil.rmtree(folder)

    def save_error_log(self):
        """
        Save last 60 screenshots in ./log/error/<config-name>/<timestamp>
        Save logs to ./log/error/<config-name>/<timestamp>/log.txt
        """
        import pathlib
        from module.base.utils import save_image
        from module.handler.sensitive_info import (handle_sensitive_image,
                                                   handle_sensitive_logs)
        if self.config.Error_SaveError:
            config_folder = pathlib.Path(f"./log/error/{self.config_name}")
            folder = config_folder.joinpath(str(int(time.time() * 1000)))
            folder.mkdir(parents=True, exist_ok=True)
            logger.warning(f'Saving error: {folder}')

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
            self.keep_last_errlog(config_folder, self.config.Error_SaveErrorCount)

    def restart(self):
        from module.handler.login import LoginHandler
        LoginHandler(self.config, device=self.device).app_restart()
        self.config.task_delay(server_update=True)

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

    def awaken(self):
        from module.awaken.awaken import Awaken
        Awaken(config=self.config, device=self.device).run()

    def shop_frequent(self):
        from module.shop.shop_reward import RewardShop
        RewardShop(config=self.config, device=self.device).run_frequent()

    def shop_once(self):
        from module.shop.shop_reward import RewardShop
        RewardShop(config=self.config, device=self.device).run_once()

    def event_shop(self):
        from module.shop_event.shop_event import EventShop
        EventShop(config=self.config, device=self.device).run()

    def shipyard(self):
        from module.shipyard.shipyard_reward import RewardShipyard
        RewardShipyard(config=self.config, device=self.device).run()

    def gacha(self):
        from module.gacha.gacha_reward import RewardGacha
        RewardGacha(config=self.config, device=self.device).run()

    def freebies(self):
        from module.freebies.freebies import Freebies
        Freebies(config=self.config, device=self.device).run()

    def minigame(self):
        from module.minigame.minigame import Minigame
        Minigame(config=self.config, device=self.device).run()

    def private_quarters(self):
        from module.private_quarters.private_quarters import PrivateQuarters
        PrivateQuarters(config=self.config, device=self.device).run()

    def island(self):
        from module.island.island import Island
        Island(config=self.config, device=self.device).run()

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

    def event_a(self):
        from module.event.campaign_abcd import CampaignABCD
        CampaignABCD(config=self.config, device=self.device).run()

    def event_b(self):
        from module.event.campaign_abcd import CampaignABCD
        CampaignABCD(config=self.config, device=self.device).run()

    def event_c(self):
        from module.event.campaign_abcd import CampaignABCD
        CampaignABCD(config=self.config, device=self.device).run()

    def event_d(self):
        from module.event.campaign_abcd import CampaignABCD
        CampaignABCD(config=self.config, device=self.device).run()

    def event_sp(self):
        from module.event.campaign_sp import CampaignSP
        CampaignSP(config=self.config, device=self.device).run()

    def maritime_escort(self):
        from module.event.maritime_escort import MaritimeEscort
        MaritimeEscort(config=self.config, device=self.device).run()

    def opsi_ash_assist(self):
        from module.os_ash.meta import AshBeaconAssist
        AshBeaconAssist(config=self.config, device=self.device).run()

    def opsi_ash_beacon(self):
        from module.os_ash.meta import OpsiAshBeacon
        OpsiAshBeacon(config=self.config, device=self.device).run()

    def opsi_explore(self):
        from module.campaign.os_run import OSCampaignRun
        OSCampaignRun(config=self.config, device=self.device).opsi_explore()

    def opsi_shop(self):
        from module.campaign.os_run import OSCampaignRun
        OSCampaignRun(config=self.config, device=self.device).opsi_shop()

    def opsi_voucher(self):
        from module.campaign.os_run import OSCampaignRun
        OSCampaignRun(config=self.config, device=self.device).opsi_voucher()

    def opsi_daily(self):
        from module.campaign.os_run import OSCampaignRun
        OSCampaignRun(config=self.config, device=self.device).opsi_daily()

    def opsi_obscure(self):
        from module.campaign.os_run import OSCampaignRun
        OSCampaignRun(config=self.config, device=self.device).opsi_obscure()

    def opsi_month_boss(self):
        from module.campaign.os_run import OSCampaignRun
        OSCampaignRun(config=self.config, device=self.device).opsi_month_boss()

    def opsi_abyssal(self):
        from module.campaign.os_run import OSCampaignRun
        OSCampaignRun(config=self.config, device=self.device).opsi_abyssal()

    def opsi_archive(self):
        from module.campaign.os_run import OSCampaignRun
        OSCampaignRun(config=self.config, device=self.device).opsi_archive()

    def opsi_stronghold(self):
        from module.campaign.os_run import OSCampaignRun
        OSCampaignRun(config=self.config, device=self.device).opsi_stronghold()

    def opsi_meowfficer_farming(self):
        from module.campaign.os_run import OSCampaignRun
        OSCampaignRun(config=self.config, device=self.device).opsi_meowfficer_farming()

    def opsi_hazard1_leveling(self):
        from module.campaign.os_run import OSCampaignRun
        OSCampaignRun(config=self.config, device=self.device).opsi_hazard1_leveling()

    def opsi_cross_month(self):
        from module.campaign.os_run import OSCampaignRun
        OSCampaignRun(config=self.config, device=self.device).opsi_cross_month()

    def opsi_daily_delay(self):
        from module.campaign.os_run import OSCampaignRun
        OSCampaignRun(config=self.config, device=self.device).opsi_daily_delay()

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

    def raid_scuttle(self):
        from module.raid.scuttle import RaidScuttleRun
        RaidScuttleRun(config=self.config, device=self.device).run()

    def hospital(self):
        from module.event_hospital.hospital import Hospital
        Hospital(config=self.config, device=self.device).run()

    def hospital_event(self):
        from module.event_hospital.hospital_event import HospitalEvent
        HospitalEvent(config=self.config, device=self.device).run()

    def coalition(self):
        from module.coalition.coalition import Coalition
        Coalition(config=self.config, device=self.device).run()

    def coalition_sp(self):
        from module.coalition.coalition_sp import CoalitionSP
        CoalitionSP(config=self.config, device=self.device).run()

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

    def three_oil_low_cost(self):
        from module.campaign.gems_farming import GemsFarming
        GemsFarming(config=self.config, device=self.device).run(
            name=self.config.Campaign_Name, folder=self.config.Campaign_Event, mode=self.config.Campaign_Mode)

    def island_season_task(self):
        from module.island.season_task import IslandSeasonTaskHandler
        IslandSeasonTaskHandler(config=self.config, device=self.device).run()

    def daemon(self):
        from module.daemon.daemon import AzurLaneDaemon
        AzurLaneDaemon(config=self.config, device=self.device, task="Daemon").run()

    def opsi_daemon(self):
        from module.daemon.os_daemon import AzurLaneDaemon
        AzurLaneDaemon(config=self.config, device=self.device, task="OpsiDaemon").run()

    def event_story(self):
        from module.eventstory.eventstory import EventStory
        EventStory(config=self.config, device=self.device, task="EventStory").run()

    def box_disassemble(self):
        from module.storage.box_disassemble import StorageBox
        StorageBox(config=self.config, device=self.device, task="BoxDisassemble").run()

    def azur_lane_uncensored(self):
        from module.daemon.uncensored import AzurLaneUncensored
        AzurLaneUncensored(config=self.config, device=self.device, task="AzurLaneUncensored").run()

    def benchmark(self):
        from module.daemon.benchmark import run_benchmark
        run_benchmark(config=self.config)

    def game_manager(self):
        from module.daemon.game_manager import GameManager
        GameManager(config=self.config, device=self.device, task="GameManager").run()

    def wait_until(self, future):
        """
        Wait until a specific time.

        Args:
            future (datetime):

        Returns:
            bool: True if wait finished, False if config changed.
        """
        future = future + timedelta(seconds=1)
        self.config.start_watching()
        while 1:
            if datetime.now() > future:
                return True
            if self.stop_event is not None:
                if self.stop_event.is_set():
                    logger.info("Update event detected")
                    logger.info(f"[{self.config_name}] exited. Reason: Update")
                    exit(0)

            time.sleep(5)

            if self.config.should_reload():
                return False

    def get_next_task(self):
        """
        Returns:
            str: Name of the next task.
        """
        while 1:
            task = self.config.get_next()
            self.config.task = task
            self.config.bind(task)

            from module.base.resource import release_resources
            if self.config.task.command != 'Alas':
                release_resources(next_task=task.command)

            if task.next_run > datetime.now():
                logger.info(f'Wait until {task.next_run} for task `{task.command}`')
                self.is_first_task = False
                method = self.config.Optimization_WhenTaskQueueEmpty
                if method == 'close_game':
                    logger.info('Close game during wait')
                    self.device.app_stop()
                    release_resources()
                    self.device.release_during_wait()
                    if not self.wait_until(task.next_run):
                        del_cached_property(self, 'config')
                        continue
                    if task.command != 'Restart':
                        self.config.task_call('Restart')
                        del_cached_property(self, 'config')
                        continue
                elif method == 'goto_main':
                    logger.info('Goto main page during wait')
                    self.run('goto_main')
                    release_resources()
                    self.device.release_during_wait()
                    if not self.wait_until(task.next_run):
                        del_cached_property(self, 'config')
                        continue
                elif method == 'stay_there':
                    logger.info('Stay there during wait')
                    release_resources()
                    self.device.release_during_wait()
                    if not self.wait_until(task.next_run):
                        del_cached_property(self, 'config')
                        continue
                else:
                    logger.warning(f'Invalid Optimization_WhenTaskQueueEmpty: {method}, fallback to stay_there')
                    release_resources()
                    self.device.release_during_wait()
                    if not self.wait_until(task.next_run):
                        del_cached_property(self, 'config')
                        continue
            break

        AzurLaneConfig.is_hoarding_task = False
        return task.command

    def loop(self):
        logger.set_file_logger(self.config_name)
        logger.info(f'Start scheduler loop: {self.config_name}')

        # --- 初始化计数器 ---
        consecutive_global_failures = 0
        MAX_GLOBAL_FAILURES = 3     # 3 or more，4次及以上会执行长达5分钟的防网络波动等待
        RESTART_DELAY = 20     # 重启尝试间隔
        LONG_WAIT = 300

        while 1:
            try:
                # Check update event from GUI
                if self.stop_event is not None:
                    if self.stop_event.is_set():
                        logger.info("Update event detected")
                        logger.info(f"Alas [{self.config_name}] exited.")
                        break
                # Check game server maintenance
                self.checker.wait_until_available()
                if self.checker.is_recovered():
                    # There is an accidental bug hard to reproduce
                    # Sometimes, config won't be updated due to blocking
                    # even though it has been changed
                    # So update it once recovered
                    del_cached_property(self, 'config')
                    logger.info('Server or network is recovered. Restart game client')
                    self.config.task_call('Restart')
                # Check scheduled emulator restart (between tasks, won't interrupt running task)
                if self.config.EmulatorManagement_ScheduledEmulatorRestart:
                    elapsed_hours = (time.time() - self.last_emulator_restart_time) / 3600
                    interval = self.config.EmulatorManagement_RestartIntervalHours
                    if elapsed_hours >= interval:
                        logger.hr('Scheduled Emulator Restart', level=1)
                        logger.info(f'Emulator has been running for {elapsed_hours:.1f} hours, '
                                    f'scheduled restart interval is {interval} hours')
                        if self._try_restart_emulator():
                            self.last_emulator_restart_time = time.time()
                            self.config.task_call('Restart')
                            del_cached_property(self, 'config')
                            continue
                        else:
                            logger.warning('Scheduled emulator restart failed, continuing normally')

                # Get task
                task = self.get_next_task()
                # Init device and change server
                _ = self.device
                self.device.config = self.config
                # Skip first restart
                if self.is_first_task and task == 'Restart':
                    logger.info('Skip task `Restart` at scheduler start')
                    self.config.task_delay(server_update=True)
                    del_cached_property(self, 'config')
                    continue

                # Run
                logger.info(f'Scheduler: Start task `{task}`')
                self.device.stuck_record_clear()
                self.device.click_record_clear()
                logger.hr(task, level=0)
                success = self.run(inflection.underscore(task))
                logger.info(f'Scheduler: End task `{task}`')
                self.is_first_task = False

                # Check failures
                # @ 单个任务连续失败三次终止程序
                # 注意：可恢复错误 (success == 'recoverable') 不计入失败次数
                failed = deep_get(self.failure_record, keys=task, default=0)
                if success == True:
                    failed = 0  # 成功，重置计数
                elif success == 'recoverable':
                    # 可恢复错误（如 GameStuckError），不增加失败计数
                    # 但也不重置，保持之前的计数
                    logger.info(f'Task `{task}` encountered a recoverable error, not counting toward failure limit')
                else:
                    failed = failed + 1  # 不可恢复错误，增加计数
                deep_set(self.failure_record, keys=task, value=failed)
                
                strict_restart = self.config.Error_StrictRestart and failed >= 1 and task in RESTART_SENSITIVE_TASKS
                if failed >= 3 or strict_restart:
                    logger.critical(f"Task `{task}` failed {failed} or more times.")
                    logger.critical("Possible reason #1: You haven't used it correctly. "
                                    "Please read the help text of the options.")
                    logger.critical("Possible reason #2: There is a problem with this task. "
                                    "Please contact developers or try to fix it yourself.")
                    if strict_restart:
                        logger.critical("Possible reason #3: This is a restart sensitive task. "
                                        "Please take over the game manually or turn off 'StrictRestart' option.")
                    logger.critical('Request human takeover')
                    handle_notify(
                        self.config.Error_OnePushConfig,
                        title=f"Alas <{self.config_name}> crashed",
                        content=f"<{self.config_name}> RequestHumanTakeover\nTask `{task}` failed {failed} or more times.",
                    )
                    logger.warning("任务连续失败次数过多，正在上报错误日志...")
                    ApiClient.submit_bug_log(f"Alas <{self.config_name}> crashed\nTask `{task}` failed {failed} or more times.")
                    exit(1)

                if success == True:
                    del_cached_property(self, 'config')
                    consecutive_global_failures = 0 # Reset global failure counter on successful task
                    self.consecutive_game_stuck = 0
                    self.consecutive_adb_offline = 0
                    continue
                elif success == 'recoverable' or self.config.Error_HandleError:
                    # 可恢复错误或启用了错误处理，继续循环
                    # self.config.task_delay(success=False)
                    del_cached_property(self, 'config')
                    self.checker.check_now()
                    continue
                else:
                    break
            
            # --- 新增代码：捕获全局异常并执行重启 ---
            except Exception as e:
                consecutive_global_failures += 1
                self.is_first_task = False
                logger.error("An unexpected global exception occurred in the scheduler loop!")
                import traceback
                logger.error(traceback.format_exc()) # 打印完整的错误堆栈
                logger.warning(
                    f">>> This is consecutive global failure #{consecutive_global_failures} of {MAX_GLOBAL_FAILURES}."
                )

                # --- 检查是否达到重试上限 ---
                if consecutive_global_failures >= MAX_GLOBAL_FAILURES:
                    logger.critical(
                        f"Maximum number of consecutive global failures ({MAX_GLOBAL_FAILURES}) reached."
                    )
                    logger.critical("The error appears to be fatal and unrecoverable by restarting.")
                    self.save_error_log()
                    logger.critical("Scheduler is now terminating. Manual intervention is required.")
                    logger.warning("遇到无法恢复的致命错误，正在上报错误日志...")
                    ApiClient.submit_bug_log(f"Alas <{self.config_name}> Scheduler terminating.\nMaximum global failures ({MAX_GLOBAL_FAILURES}) reached.\n{traceback.format_exc()}")
                    exit(1)   # 达到上限，强制终止程序

                 # --- 尝试重启 ---
                logger.warning("Attempting to recover by forcing a RESTART task...")
                try:
                    # 注入 Restart 任务
                    self.config.task_call('Restart')
                    # 重新加载配置
                    del_cached_property(self, 'config')
                    logger.info("A `Restart` task has been scheduled for the next loop.")
                except Exception as restart_e:
                    logger.error("Failed to even schedule a restart task!")
                    logger.error(f"Scheduling Error: {restart_e}")

                # --- 等待一段时间后开始下一次循环 ---
                wait_seconds = RESTART_DELAY if consecutive_global_failures < 4 else LONG_WAIT
                logger.info(
                    f"Scheduler will retry from the beginning in {wait_seconds} seconds."
                )
                time.sleep(wait_seconds)

if __name__ == '__main__':
    alas = AzurLaneAutoScript()
    alas.loop()
