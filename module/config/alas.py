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
from module.config.config_manager import Config, TaskEnd


class AzurLaneAutoScript:
    def __init__(self, config_name='alas'):
        self.config_name = config_name
        self.config = Config(config_name)
        self.device = Device(config=self.config)

    def run(self, command):
        logger.attr('Command', command)
        while 1:
            try:
                self.__getattribute__(command)()
                return True
            except TaskEnd as e:
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

    def loop(self):
        while 1:
            self.config.update()
            task = self.config.get_next()
            self.run(task)


scheduler = AzurLaneAutoScript()
scheduler.loop()
