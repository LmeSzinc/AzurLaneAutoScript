import copy
import datetime
import operator
import time

from module.base.filter import Filter
from module.base.utils import ensure_time
from module.config.config_generated import GeneratedConfig
from module.config.config_manual import ManualConfig
from module.config.utils import *
from module.exception import RequestHumanTakeover, ScriptError
from module.logger import logger


class TaskEnd(Exception):
    pass


class Function:
    def __init__(self, data):
        self.enable = deep_get(data, keys='Scheduler.Enable', default=False)
        self.command = deep_get(data, keys='Scheduler.Command', default='Unknown')
        self.next_run = deep_get(data, keys='Scheduler.NextRun', default=datetime(2020, 1, 1, 0, 0))


class AzurLaneConfig(ManualConfig, GeneratedConfig):
    # This will read ./config/<config_name>.yaml
    config_name = ''
    # Raw json data in yaml file.
    data = {}
    # Task to run and bind.
    # Task means the name of the function to run in AzurLaneAutoScript class.
    task = ''
    # Modified arguments. Key: Argument path in yaml file. Value: Modified value.
    # All variable modifications will be record here and saved in method `save()`.
    modified = {}
    # Key: Argument name in GeneratedConfig. Value: Path in `data`.
    bound = {}
    # If write after every variable modification.
    auto_update = True
    # Force override variables
    # Key: Argument name in GeneratedConfig. Value: Modified value.
    overridden = {}

    def __setattr__(self, key, value):
        if key in self.bound:
            path = self.bound[key]
            self.modified[path] = value
            if self.auto_update:
                self.update()
        else:
            super().__setattr__(key, value)

    def __init__(self, config_name, task=None):
        self.config_name = config_name
        self.load()
        if task is None:
            task = self.get_next()
        self.bind(task)
        logger.info(f'Bind task {task}')
        self.task = task

    def load(self):
        self.data = read_file(filepath_config(self.config_name))

    def bind(self, func):
        """
        Args:
            func (str): Function to run
        """
        func_list = [func, 'General', 'Alas']

        # Bind arguments
        visited = set()
        self.bound = {}
        for func in func_list:
            func_data = self.data.get(func, {})
            for group, group_data in func_data.items():
                for arg, value in group_data.items():
                    path = f'{group}.{arg}'
                    if path in visited:
                        continue
                    arg = path_to_arg(path)
                    super().__setattr__(arg, value)
                    self.bound[arg] = f'{func}.{path}'
                    visited.add(path)

        # Override arguments
        for arg, value in self.overridden.items():
            super().__setattr__(arg, value)

    def _func_check(self, function):
        """
        Args:
            function (Function):

        Returns:
            bool:
        """
        if not function.enable:
            return False

        return True

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
            pending = f.apply(pending, func=self._func_check)
            pending = [f.command for f in pending]
            if pending:
                logger.info(f'Pending tasks: {pending}')
                task = pending[0]
                logger.attr('Task', task)
                return task

        if waiting:
            waiting = sorted(waiting, key=operator.attrgetter('next_run'))[0]
            logger.info('No task pending')
            logger.info(f'Wait until {waiting.next_run} for task `{waiting.command}`')

            time.sleep(waiting.next_run.timestamp() - datetime.now().timestamp() + 1)
            return self.get_next()
        else:
            logger.critical('No task waiting or pending')
            logger.critical('Please enable at least one task')
            raise RequestHumanTakeover

    def save(self):
        if not self.modified:
            return False

        for path, value in self.modified.items():
            deep_set(self.data, keys=path, value=value)

        logger.info(f'Save config {filepath_config(self.config_name)}, {dict_to_kv(self.modified)}')
        self.modified = {}
        write_file(filepath_config(self.config_name), data=self.data)

    def update(self):
        self.load()
        self.bind(self.task)
        self.save()

    def override(self, **kwargs):
        """
        Override anything you want.
        Variables stall remain overridden even config is reloaded from yaml file.
        Note that this method is irreversible.
        """
        for arg, value in kwargs.items():
            self.overridden[arg] = value
            super().__setattr__(arg, value)

    def set_record(self, **kwargs):
        """
        Args:
            **kwargs: For example, `Emotion1_Value=150`
                will set `Emotion1_Value=150` and `Emotion1_Record=now()`
        """
        self.auto_update = False

        for arg, value in kwargs.items():
            group, _ = arg.split('_', 1)
            record = f'{group}_Record'
            self.__setattr__(arg, value)
            self.__setattr__(record, datetime.now().replace(microsecond=0))

        self.update()
        self.auto_update = True

    def task_delay(self, success=None, server_update=None, target=None, minute=None):
        """
        Set Scheduler.NextRun
        Should set at least one arguments.
        If multiple arguments are set, use the nearest.

        Args:
            success (bool):
                If True, delay Scheduler.SuccessInterval
                If False, delay Scheduler.FailureInterval
            server_update (bool, list, str):
                If True, delay to nearest Scheduler.ServerUpdate
                If type is list or str, delay to such server update
            target (datetime.datetime, str, list):
                Delay to such time.
            minute (int, float, tuple):
                Delay several minutes.
        """

        def ensure_delta(delay):
            return timedelta(seconds=int(ensure_time(delay, precision=3) * 60))

        run = []
        if success is not None:
            interval = self.Scheduler_SuccessInterval if success else self.Scheduler_FailureInterval
            run.append(datetime.now() + ensure_delta(interval))
        if server_update is not None:
            if server_update is True:
                server_update = self.Scheduler_ServerUpdate
            run.append(get_server_next_update(server_update))
        if target is not None:
            target = [target] if not isinstance(target, list) else target
            target = nearest_future(target)
            run.append(target)
        if minute is not None:
            run.append(datetime.now() + ensure_delta(minute))

        if len(run):
            run = min(run).replace(microsecond=0)
            kv = dict_to_kv(
                {'success': success, 'server_update': server_update, 'target': target, 'minute': minute},
                allow_none=False)
            logger.info(f'Delay task `{self.task}` to {run} ({kv})')
            self.Scheduler_NextRun = run
        else:
            raise ScriptError('Missing argument in delay_next_run, should set at least one')

    def task_call(self, task):
        """
        Call another task to run.

        That task will run when current task finished.
        But it might not be run because:
        - Other tasks should run first according to SCHEDULER_PRIORITY
        - Task is disabled by user

        Args:
            task (str): Task name to call, such as `Restart`
        """
        path = f'{task}.Scheduler.NextRun'
        if deep_get(self.data, keys=path, default=None) is None:
            raise ScriptError(f'Task to call: `{task}` does not exist in user config')
        else:
            self.modified[path] = datetime.now().replace(microsecond=0)
            if task == 'Restart':
                # Restart is forced to enable
                self.modified[f'{task}.Scheduler.Enable'] = True
            self.update()

    def task_stop(self, message=''):
        """
        Stop current task

        Raises:
            TaskEnd:
        """
        if message:
            raise TaskEnd(message)
        else:
            raise TaskEnd

    def task_switched(self):
        """
        Check if needs to switch task.

        Raises:
            bool: If task switched
        """
        prev = self.task
        self.load()
        new = self.get_next()
        if prev != new:
            logger.info(f'Switch task `{prev}` to `{new}`')
            return True
        else:
            return False

    @property
    def campaign_name(self):
        """
        Sub-directory name when saving drop record.
        """
        name = self.Campaign_Name.lower().replace('-', '_')
        if name[0].isdigit():
            name = 'campaign_' + str(name)
        if self.Campaign_Mode == 'hard':
            name += '_hard'
        return name

    """
    The following configs and methods are used to be compatible with the old.
    """

    def merge(self, other):
        """
        Args:
            other (AzurLaneConfig, Config):

        Returns:
            AzurLaneConfig
        """
        config = copy.copy(self)
        for attr in dir(config):
            if attr.endswith('__'):
                continue
            if hasattr(other, attr):
                value = other.__getattribute__(attr)
                if value is not None:
                    config.__setattr__(attr, value)

        return config

    @property
    def DEVICE_SCREENSHOT_METHOD(self):
        return self.Emulator_ScreenshotMethod

    @property
    def DEVICE_CONTROL_METHOD(self):
        return self.Emulator_ControlMethod

    @property
    def FLEET_1(self):
        return self.Fleet_Fleet1

    @property
    def FLEET_2(self):
        return self.Fleet_Fleet2

    _fleet_boss = 0

    @property
    def FLEET_BOSS(self):
        if self._fleet_boss:
            return self._fleet_boss
        if self.Fleet_FleetOrder == 'fleet1_mob_fleet2_boss':
            return 2
        else:
            return 1

    @FLEET_BOSS.setter
    def FLEET_BOSS(self, value):
        self._fleet_boss = value
