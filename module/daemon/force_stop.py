from module.handler.login import LoginHandler
from module.logger import logger


class ForceStop(LoginHandler):
    def force_stop(self):
        logger.hr('Force Stop AzurLane', level=1)
        self.device.app_stop()
        logger.info('Force Stop finished')


if __name__ == '__main__':
    ForceStop('alas', task='ForceStop').force_stop()
