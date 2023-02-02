from module.logger import logger
from module.config.utils import deep_get, deep_set
from datetime import datetime


class LogRes:

    def __init__(self, config):
        self.config=config

    def log_res(self, num, name):
        Res = [
            'Oil',
            'Coin',
            'Gem',
            'Cube',
            'Pt',
            'ActionPoint',
            'YellowCoin',
            'PurpleCoin',
        ]
        EquipProgress = ['457mm', '234mm', 'tenrai', '152mm']
        if name in Res:
            key = f'Res.Res.{name}'
            original = deep_get(self.config.data, keys=key)
            if num == original:
                return False
            key_time = f'Res.Res.' + name + 'Time'
            _time = datetime.now()
            time = str(_time)
            self.config.modified[key_time] = time[:19]
            self.config.modified[key] = num
            self.config.update()
        elif name in EquipProgress:
            key = f'EquipProgress.EquipProgress.{name}'
            deep_set(d=self.config.data, keys=key, value=num)
            self.config.data.save()
        else:
            logger.warn('No such resource!')
        return True
