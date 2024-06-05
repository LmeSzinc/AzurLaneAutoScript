from module.handler.login import LoginHandler
from module.logger import logger
<<<<<<< HEAD
from module.gg_handler.gg_handler import GGHandler
=======
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0


class GameManager(LoginHandler):
    def run(self):
        logger.hr('Force Stop AzurLane', level=1)
        self.device.app_stop()
        logger.info('Force Stop finished')
<<<<<<< HEAD
        GGHandler(config=self.config, device=self.device).check_config()
        if self.config.GameManager_AutoRestart:
            LoginHandler(config=self.config, device=self.device).app_restart()
=======

        if self.config.GameManager_AutoRestart:
            self.device.app_start()
            self.handle_app_login()
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0


if __name__ == '__main__':
    GameManager('alas', task='GameManager').run()
