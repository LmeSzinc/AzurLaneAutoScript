from cached_property import cached_property
from module.logger import logger
from module.config.utils import deep_get


class LogRes:

    def __init__(self, config):
        self.config = config

    @cached_property
    def groups(self) -> dict:
        from module.config.utils import read_file, filepath_argument
        return deep_get(d=read_file(filepath_argument("dashboard")), keys='Dashboard')

    def log_res(self, name, modified: dict):
        if name in self.groups:
            key = f'Dashboard.{name}'
            original = deep_get(self.config.data, keys=key)
            _mod = False
            for value_name, value in modified.items():
                if value == original[value_name]:
                    continue
                _key = key+f'.{value_name}'
                self.config.modified[_key] = value
                _mod = True
            if _mod:
                _key_time = key+f'.Record'
                from datetime import datetime
                _time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.config.modified[_key_time] = _time
                self.config.update()
        else:
            logger.warning('No such resource!')
        return True


if __name__ == '__main__':
    from module.config.config import AzurLaneConfig
    LogRes(AzurLaneConfig('alas2')).log_res(name='Oil', modified={'Value': 20000, 'Limit': 10000})
