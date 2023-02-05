from cached_property import cached_property
from module.logger import logger
from module.config.utils import deep_get


class LogRes:

    def __init__(self, config):
        self.config = config
        # self.data = data
        _ = self.arg_path

    def arg_name_to_path(self, funcs):
        arg_path = {}
        for func in funcs:
            for group in self.config.data[func]:
                for value_name, value in self.config.data[func][group].items():
                    key = f'{func}.{group}.{value_name}'
                    arg_path = {**arg_path, **{value_name: key}}
        return arg_path
    @cached_property
    def arg_path(self):
        from module.config.utils import read_file, filepath_argument
        return self.arg_name_to_path(read_file(filepath_argument("dashboard")))

    def log_res(self, num, name):
        if name in self.arg_path:
            key = self.arg_path[name]
            original = deep_get(self.config.data, keys=key)
            if num == original:
                return False
            if not ('Limit' in key or 'Total' in key):
                key_time = key.replace('Value', 'Record')
                from datetime import datetime
                _time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                time = str(_time)
                self.config.modified[key_time] = time
            self.config.modified[key] = num
            self.config.update()
        else:
            logger.warning('No such resource!')
        return True


if __name__ == '__main__':
    from module.config.config import AzurLaneConfig
    from module.config.utils import data_to_path
    data1 = data_to_path(AzurLaneConfig(config_name='alas2').data)
    data2 = LogRes(AzurLaneConfig(config_name='alas2')).arg_path
    print(data1)
    print(data2)
