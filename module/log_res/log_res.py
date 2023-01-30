import datetime

from module.logger import logger
from module.config.utils import deep_set


class log_res:

    def __init__(self, config):
        self.config=config

    def log_res(self, num, name):
        ViewCurrentResources = [
            'oil',
            'coin',
            'gem',
            'pt',
            'opcoin',
            'purplecoin',
            'actionpoint',
            'cube',
            'maxoil',
            'maxcoin',
            'oiltomaxoil',
            'cointomaxcoin'
        ]
        ViewEquipProgress = ['457mm', '234mm', 'tenrai', '152mm']
        if name in ViewCurrentResources:
            key = f'ViewCurrentResources.ViewCurrentResources.{name}'
            key_time = f'ViewCurrentResources.ViewCurrentResources.' + name + 'Time'
            from datetime import datetime
            _time = datetime.now()
            time = str(_time)
            deep_set(d=self.config.data, keys=key_time, value=time[:19])
            deep_set(d=self.config.data, keys=key, value=num)
            self.config.write_file(self.config.config_name, data=self.config.data)
            self.config.data = self.config.read_file(self.config.config_name)
        elif name in ViewEquipProgress:
            key = f'ViewCurrentResources.ViewEquipProgress.{name}'
            deep_set(d=self.config.data, keys=key, value=num)
            self.config.data.save()
        else:
            logger.warn('No such resource!')
        return None
