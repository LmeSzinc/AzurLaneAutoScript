from module.config.config import AzurLaneConfig, deep_get
from module.base.base import ModuleBase


class gg_data(ModuleBase):
    gg_on = False
    gg_enable = False
    gg_auto = False
    ggdata = {}

    def __init__(self, config=None, target=None, value=None):
        if config != None:
            super().__init__(config)
            self.target = target
            self.value = value
            import os
            if not os.path.exists('./config/gg_handler'):
                os.mkdir('./config/gg_handler')
            with open(file=f'./config/gg_handler/gg_data_{self.config.config_name}.tmp',
                      mode='a+',
                      encoding='utf-8') as tmp:
                tmp.close()
            tmp = open(file=f'./config/gg_handler/gg_data_{self.config.config_name}.tmp',
                       mode='r',
                       encoding='utf-8')
            line = tmp.readline()
            if line[:-1] != self.config.config_name:
                tmp.close()
                tmp = open(file=f'./config/gg_handler/gg_data_{self.config.config_name}.tmp',
                           mode='w',
                           encoding='utf-8')
                tmp.write(f'{self.config.config_name}\n')
                tmp.write('gg_on=False\n')
                self.ggdata['gg_on'] = False
                self.ggdata['gg_enable'] = deep_get(d=self.config.data,
                                                    keys='GameManager.GGHandler.Enabled',
                                                    default=False)
                self.ggdata['gg_auto'] = deep_get(d=self.config.data,
                                                  keys='GameManager.GGHandler.AutoRestartGG',
                                                  default=False)
                tmp.write('gg_enable=' + str(self.ggdata['gg_enable']) + '\n')
                tmp.write('gg_auto=' + str(self.ggdata['gg_auto']) + '\n')
                tmp.close()
                if not deep_get(d=self.config.data, keys='GameManager.GGHandler.RestartEverytime', default=True):
                    from module.handler.login import LoginHandler
                    LoginHandler(config=self.config, device=self.device).app_restart()
            else:
                for i in range(3):
                    line = tmp.readline()
                    line1, line2 = line.split('=')
                    self.ggdata[line1] = True if line2[:-1] == 'True' else False
                tmp.close()

        else:
            from module.logger import logger
            logger.warning('No config data, assume in need of deleting temp')

    def get_data(self):
        # Return a dict of data
        return self.ggdata

    def set_data(self):
        self.ggdata[self.target] = self.value
        self.update_data()

    def update_data(self):
        with open(file=f'./config/gg_handler/gg_data_{self.config.config_name}.tmp',
                  mode='w',
                  encoding='utf-8') as tmp:
            tmp.write(f'{self.config.config_name}\n')
            for t in self.ggdata:
                tmp.write(t + '=' + str(self.ggdata[t]) + '\n')
        tmp.close()

    def dele(self):
        with open(file=f'./config/gg_handler/gg_data_{self.config.config_name}.tmp',
                  mode='w',
                  encoding='utf-8') as tmp:
            tmp.write('啊吧啊吧')
        tmp.close()


# if __name__ == '__main__':
#     config = AzurLaneConfig(config_name='alas')
#     print(gg_data(config).get_data())
#     gg_data(config=config, target='gg_on', value=True).set_data()
#     print(gg_data(config).get_data())
#     gg_data().dele()
