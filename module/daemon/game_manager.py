from module.handler.login import LoginHandler
from module.logger import logger
from module.config.config import deep_get
from module.gg_handler.gg_data import gg_data


class GameManager(LoginHandler):
    def run(self):
        logger.hr('Force Stop AzurLane', level=1)
        self.device.app_stop()
        logger.info('Force Stop finished')
        gg_enable = deep_get(d=self.config.data, keys='GameManager.GGHandler.Enabled', default=False)
        gg_auto = deep_get(d=self.config.data, keys='GameManager.GGHandler.AutoRestartGG', default=False)
        gg_data(self.config, target='gg_enable', value=gg_enable).set_data()
        gg_data(self.config, target='gg_auto', value=gg_auto).set_data()
        ggdata = gg_data(self.config).get_data()
        logger.info(f'GG status:')
        logger.info(f'Enabled={ggdata["gg_enable"]} AutoRestart={ggdata["gg_auto"]} Current stage={ggdata["gg_on"]}')
        if self.config.GameManager_AutoRestart:
            self.device.app_start()
            LoginHandler(config=self.config, device=self.device).app_restart()


if __name__ == '__main__':
    GameManager('alas', task='GameManager').run()
