from module.handler.login import LoginHandler
from module.logger import logger


class GameManager(LoginHandler):
    def run(self):
        logger.hr('Force Stop AzurLane', level=1)
        self.device.app_stop()
        # self.handle_app_login()
        logger.info('Force Stop finished')

        if self.config.GameManager_AutoRestart:
            self.device.app_start()
            self.handle_app_login()
            logger.info('Auto Restart AzurLane')


if __name__ == '__main__':
    GameManager('alas', task='GameManager').run()
