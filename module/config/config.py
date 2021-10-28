import datetime
import operator
import time

from module.base.filter import Filter
from module.base.utils import ensure_time
from module.config.config_generated import GeneratedConfig
from module.config.config_manual import ManualConfig
from module.config.config_updater import ConfigUpdater
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

    def __str__(self):
        return f'{self.command} ({self.enable}, {str(self.next_run)})'

    __repr__ = __str__


class AzurLaneConfig(ConfigUpdater, ManualConfig, GeneratedConfig):
    bound = {}

    # Class property
    is_hoarding_task = True

    def __setattr__(self, key, value):
        if key in self.bound:
            path = self.bound[key]
            self.modified[path] = value
            if self.auto_update:
                self.update()
        else:
            super().__setattr__(key, value)

    def __init__(self, config_name, task=None):
        logger.attr('Server', server.server)
        # This will read ./config/<config_name>.json
        self.config_name = config_name
        # Raw json data in yaml file.
        self.data = {}
        # Modified arguments. Key: Argument path in yaml file. Value: Modified value.
        # All variable modifications will be record here and saved in method `save()`.
        self.modified = {}
        # Key: Argument name in GeneratedConfig. Value: Path in `data`.
        self.bound = {}
        # If write after every variable modification.
        self.auto_update = True
        # Force override variables
        # Key: Argument name in GeneratedConfig. Value: Modified value.
        self.overridden = {}
        # Scheduler queue, will be updated in `get_next_task()`, list of Function objects
        # pending_task: Run time has been reached, but haven't been run due to task scheduling.
        # waiting_task: Run time haven't been reached, wait needed.
        self.pending_task = []
        self.waiting_task = []
        # Task to run and bind.
        # Task means the name of the function to run in AzurLaneAutoScript class.
        if config_name == 'template':
            # For dev tools
            logger.info('Using template config, which is read only')
            self.auto_update = False
            self.task = 'template'
        else:
            self.load()
            if task is None:
                task = self.get_next()
            self.bind(task)
            logger.info(f'Bind task {task}')
            self.task = task

    def load(self):
        self.data = self.read_file(self.config_name)

        for path, value in self.modified.items():
            deep_set(self.data, keys=path, value=value)

    def bind(self, func):
        """
        Args:
            func (str): Function to run
        """
        func_set = {func, 'General', 'Alas'}
        if 'opsi' in func.lower():
            func_set.add('OpsiGeneral')

        # Bind arguments
        visited = set()
        self.bound = {}
        for func in func_set:
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

    @property
    def hoarding(self):
        return timedelta(minutes=deep_get(self.data, keys='Alas.Optimization.TaskHoardingDuration', default=0))

    @property
    def close_game(self):
        return deep_get(self.data, keys='Alas.Optimization.CloseGameDuringWait', default=False)

    def get_next_task(self):
        """
        Calculate tasks, set pending_task and waiting_task
        """
        pending = []
        waiting = []
        now = datetime.now()
        if AzurLaneConfig.is_hoarding_task:
            now -= self.hoarding
        for func in self.data.values():
            func = Function(func)
            if func.next_run < now:
                pending.append(func)
            else:
                waiting.append(func)

        if pending:
            f = Filter(regex=r'(.*)', attr=['command'])
            f.load(self.SCHEDULER_PRIORITY)
            pending = f.apply(pending, func=lambda x: x.enable)
        if waiting:
            waiting = sorted(waiting, key=operator.attrgetter('next_run'))

        self.pending_task = pending
        self.waiting_task = waiting

    def get_next(self):
        """
        Returns:
            str: Command to run
        """
        self.get_next_task()

        if self.pending_task:
            AzurLaneConfig.is_hoarding_task = False
            pending = [f.command for f in self.pending_task]
            logger.info(f'Pending tasks: {pending}')
            self.pending_task = pending
            task = pending[0]
            logger.attr('Task', task)
            return task
        else:
            AzurLaneConfig.is_hoarding_task = True

        if self.waiting_task:
            task = self.waiting_task[0]
            target = (task.next_run + self.hoarding).replace(microsecond=0)
            logger.info('No task pending')
            logger.info(f'Wait until {target} for task `{task.command}`')
            if self.close_game:
                self.modified['Restart.Scheduler.Enable'] = True
                self.modified['Restart.Scheduler.NextRun'] = target
                self.task = 'Restart'
                self.update()
                return 'Restart'
            else:
                time.sleep(task.next_run.timestamp() - datetime.now().timestamp() + 1)
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
        with self.multi_set():
            for arg, value in kwargs.items():
                record = arg.replace('Value', 'Record')
                self.__setattr__(arg, value)
                self.__setattr__(record, datetime.now().replace(microsecond=0))

    def multi_set(self):
        """
        Set multiple arguments but save once.

        Examples:
            with self.config.multi_set():
                self.config.foo1 = 1
                self.config.foo2 = 2
        """
        return MultiSetWrapper(main=self)

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
            self.modified[path] = datetime(2021, 1, 1, 0, 0, 0)
            if task == 'Restart':
                # Restart is forced to enable
                self.modified[f'{task}.Scheduler.Enable'] = True
            self.update()

    @staticmethod
    def task_stop(message=''):
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

    def check_task_switch(self, message=''):
        """
        Stop current task

        Raises:
            TaskEnd:
        """
        if self.task_switched():
            self.task_stop(message=message)

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
        # Since all tasks run independently, there's no need to separate configs
        # config = copy.copy(self)
        config = self

        for attr in dir(config):
            if attr.endswith('__'):
                continue
            if hasattr(other, attr):
                value = other.__getattribute__(attr)
                if value is not None:
                    config.__setattr__(attr, value)

        return config

    @property
    def SERVER(self):
        return self.Emulator_Server

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

    @FLEET_2.setter
    def FLEET_2(self, value):
        self.override(Fleet_Fleet2=value)

    @property
    def SUBMARINE(self):
        return self.Submarine_Fleet

    @SUBMARINE.setter
    def SUBMARINE(self, value):
        self.override(Submarine_Fleet=value)

    _fleet_boss = 0

    @property
    def FLEET_BOSS(self):
        if self._fleet_boss:
            return self._fleet_boss
        if self.Fleet_Fleet2:
            if self.Fleet_FleetOrder in ['fleet1_mob_fleet2_boss', 'fleet1_boss_fleet2_mob']:
                return 2
            else:
                return 1
        else:
            return 1

    @FLEET_BOSS.setter
    def FLEET_BOSS(self, value):
        self._fleet_boss = value

    @property
    def GuildShop_PR(self):
        return [self.GuildShop_PR1, self.GuildShop_PR2, self.GuildShop_PR3]

    def temporary(self, **kwargs):
        """
        Cover some settings, and recover later.

        Usage:
        backup = self.config.cover(ENABLE_DAILY_REWARD=False)
        # do_something()
        backup.recover()

        Args:
            **kwargs:

        Returns:
            ConfigBackup:
        """
        backup = ConfigBackup(config=self)
        backup.cover(**kwargs)
        return backup


class ConfigBackup:
    def __init__(self, config):
        """
        Args:
            config (AzurLaneConfig):
        """
        self.config = config
        self.backup = {}
        self.kwargs = {}

    def cover(self, **kwargs):
        self.kwargs = kwargs
        for key, value in kwargs.items():
            self.backup[key] = self.config.__getattribute__(key)
            self.config.__setattr__(key, value)

    def recover(self):
        for key, value in self.backup.items():
            self.config.__setattr__(key, value)


class MultiSetWrapper:
    def __init__(self, main):
        """
        Args:
            main (AzurLaneConfig):
        """
        self.main = main

    def __enter__(self):
        self.main.auto_update = False
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.main.update()
        self.main.auto_update = True
