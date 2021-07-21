import os
import re
import time
from datetime import datetime

from module.config.config import AzurLaneConfig
from module.device.device import Device
from module.exception import *
from module.handler.login import LoginHandler
from module.handler.sensitive_info import handle_sensitive_image, handle_sensitive_logs
from module.logger import logger, pyw_name, log_file


class AzurLaneAutoScript:
    def __init__(self, ini_name=''):
        if not ini_name:
            ini_name = pyw_name
        ini_name = ini_name.lower()
        self.config = AzurLaneConfig(ini_name)
        self.device = None

    def run(self, command):
        logger.attr('Command', command)
        self.config.start_time = datetime.now()
        self.device = Device(config=self.config)
        while 1:
            try:
                self.__getattribute__(command.lower())()
                break
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
                break

    def save_error_log(self):
        """
        Save last 60 screenshots in ./log/error/<timestamp>
        Save logs to ./log/error/<timestamp>/log.txt
        """
        if self.config.ENABLE_ERROR_LOG_AND_SCREENSHOT_SAVE:
            folder = f'./log/error/{int(time.time() * 1000)}'
            logger.info(f'Saving error: {folder}')
            os.mkdir(folder)
            for data in logger.screenshot_deque:
                image_time = datetime.strftime(data['time'], '%Y-%m-%d_%H-%M-%S-%f')
                image = handle_sensitive_image(data['image'])
                image.save(f'{folder}/{image_time}.png')
            with open(log_file, 'r', encoding='utf-8') as f:
                start = 0
                for index, line in enumerate(f.readlines()):
                    if re.search('\+-{15,}\+', line):
                        start = index
            with open(log_file, 'r', encoding='utf-8') as f:
                text = f.readlines()[start - 2:]
                text = handle_sensitive_logs(text)
            with open(f'{folder}/log.txt', 'w', encoding='utf-8') as f:
                f.writelines(text)

    def reward_when_finished(self):
        from module.reward.reward import Reward
        az = Reward(self.config, device=self.device)
        az.reward_loop()
        self.update_check()

    def setting(self):
        for key, value in self.config.config['Setting'].items():
            if key == 'azurstat_id':
                print(f'{key} = <sensitive_infomation>')
            else:
                print(f'{key} = {value}')

        logger.hr('Settings saved')
        self.update_check()
        self.config.config_check()

    def update_check(self):
        from module.update import Update
        ad = Update(self.config)
        if self.config.UPDATE_CHECK:
            ad.get_local_commit()

    def reward(self):
        for key, value in self.config.config['Reward'].items():
            print(f'{key} = {value}')

        logger.hr('Reward Settings saved')
        self.update_check()
        self.reward_when_finished()

    def emulator(self):
        for key, value in self.config.config['Emulator'].items():
            if key == 'github_token':
                print(f'{key} = <sensitive_infomation>')
            else:
                print(f'{key} = {value}')

        logger.hr('Emulator saved')
        self.update_check()
        from module.handler.login import LoginHandler
        az = LoginHandler(self.config, device=self.device)
        if az.app_ensure_start():
            from module.reward.reward import Reward
            az = Reward(self.config, device=self.device)
            az.reward()
        else:
            az.device.screenshot()

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
        from module.reward.reward import Reward
        az = Reward(self.config, device=self.device)
        az.daily_wrapper_run()

        self.reward_when_finished()

    def event(self):
        """
        Method to run event.
        """
        from module.campaign.run import CampaignRun
        az = CampaignRun(self.config, device=self.device)
        az.run(self.config.EVENT_STAGE, folder=self.config.EVENT_NAME)
        self.reward_when_finished()

    def sos(self):
        """
        Method to SOS maps.
        """
        from module.sos.sos import CampaignSos
        az = CampaignSos(self.config, device=self.device)
        az.run()
        self.reward_when_finished()

    def war_archives(self):
        """
        Method to War Archives maps.
        """
        from module.war_archives.war_archives import CampaignWarArchives
        az = CampaignWarArchives(self.config, device=self.device)
        az.run(self.config.WAR_ARCHIVES_STAGE, folder=self.config.WAR_ARCHIVES_NAME)
        self.reward_when_finished()

    def raid(self):
        from module.raid.run import RaidRun
        az = RaidRun(self.config, device=self.device)
        az.run()
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

    def c11_affinity_farming(self):
        from module.campaign.run import CampaignRun
        az = CampaignRun(self.config, device=self.device)
        az.run('campaign_1_1_affinity_farming')
        self.reward_when_finished()

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

    def os_semi_auto(self):
        from module.daemon.os_daemon import AzurLaneDaemon
        az = AzurLaneDaemon(self.config, device=self.device)
        az.daemon()

    def os_clear_map(self):
        from module.campaign.os_run import OSCampaignRun
        az = OSCampaignRun(self.config, device=self.device)
        az.run()

    def os_world_clear(self):
        from module.campaign.os_run import OSCampaignRun
        az = OSCampaignRun(self.config, device=self.device)
        az.run_clear_os_world()
        self.reward_when_finished()

    def os_fully_auto(self):
        from module.campaign.os_run import OSCampaignRun
        az = OSCampaignRun(self.config, device=self.device)
        az.run_operation_siren()
        self.reward_when_finished()

# alas = AzurLaneAutoScript()
# alas.reward()
