import datetime
import operator
import time

from module.base.filter import Filter
from module.config.argument import Argument
from module.config.config_generated import GeneratedConfig
from module.config.config_manual import ManualConfig
from module.config.utils import *
from module.logger import logger


class TaskEnd(Exception):
    pass


class Function:
    def __init__(self, data):
        self.command = deep_get(data, keys='Scheduler.Command', default='Unknown')
        self.next_run = deep_get(data, keys='Scheduler.NextRun', default=datetime(2020, 1, 1, 0, 0))


class Config(ManualConfig, GeneratedConfig):
    config_name = ''
    data = {}
    task = ''
    _modified = {}

    def __setattr__(self, key, value):
        arg = self.__getattribute__(key)
        if isinstance(arg, Argument):
            arg.set(value)
            self._modified[arg] = value
        else:
            super().__setattr__(key, value)

    def __init__(self, config_name):
        self.config_name = config_name

    def load(self):
        self.data = read_file(filepath_config(self.config_name))

    def bind(self, func):
        """
        Args:
            func (str): Function to run
        """
        func_list = ['Alas', func]

        # Bind arguments
        visited = set()
        for func in func_list:
            func_data = self.data.get(func, {})
            for group, group_data in func_data.items():
                for arg, value in group_data.items():
                    path = f'{group}.{arg}'
                    if path in visited:
                        continue
                    arg = self.__getattribute__(path_to_arg(path))
                    arg.bind(func=func, value=value)
                    visited.add(path)

    def get_next(self):
        pending = []
        waiting = []
        for func in self.data.values():
            func = Function(func)
            if func.next_run < datetime.now():
                pending.append(func)
            else:
                waiting.append(func)

        if pending:
            f = Filter(regex=r'(.*)', attr=['command'])
            f.load(self.SCHEDULER_PRIORITY)
            pending = f.apply(pending)
            pending = [f.command for f in pending]
            if pending:
                logger.info(f'Pending tasks: {pending}')
                task = pending[0]
                logger.attr('Task', task)
                return task

        if waiting:
            waiting = sorted(waiting, key=operator.attrgetter('next_run'))[0]
            logger.info('No task pending')
            logger.info(f'Wait until {waiting.next_run} for task {waiting.command}')

            time.sleep(waiting.next_run.timestamp() - datetime.now().timestamp() + 1)
            return self.get_next()
        else:
            logger.warning('No task waiting or pending')
            exit(1)

    def save(self):
        if not self._modified:
            return False

        for arg, value in self._modified.items():
            deep_set(self.data, keys=arg.path, value=value)
            arg.set(value)

        modified = {k.path: v for k, v in self._modified.items()}
        logger.info(f'Save config {filepath_config(self.config_name)}, {dict_to_kv(modified)}')
        self._modified = {}
        write_file(filepath_config(self.config_name), data=self.data)

    def update(self):
        self.load()
        self.bind(self.task)
        self.save()
