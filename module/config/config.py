import copy
import datetime
import operator
import threading

from module.base.decorator import cached_property, del_cached_property
from module.base.filter import Filter
from module.base.utils import SelectedGrids
from module.config.config_generated import GeneratedConfig
from module.config.config_manual import ManualConfig
from module.config.config_updater import ConfigUpdater
from module.config.stored.stored_generated import StoredGenerated
from module.config.stored.classes import iter_attribute
from module.config.utils import *
from module.config.watcher import ConfigWatcher
from module.exception import RequestHumanTakeover, ScriptError
from module.logger import logger


class TaskEnd(Exception):
    pass


class Function:
    def __init__(self, data):
        self.enable = deep_get(data, keys="Scheduler.Enable", default=False)
        self.command = deep_get(data, keys="Scheduler.Command", default="Unknown")
        self.next_run = deep_get(data, keys="Scheduler.NextRun", default=DEFAULT_TIME)

    def __str__(self):
        enable = "Enable" if self.enable else "Disable"
        return f"{self.command} ({enable}, {str(self.next_run)})"

    __repr__ = __str__

    def __eq__(self, other):
        if not isinstance(other, Function):
            return False

        if self.command == other.command and self.next_run == other.next_run:
            return True
        else:
            return False


def name_to_function(name):
    """
    Args:
        name (str):

    Returns:
        Function:
    """
    function = Function({})
    function.command = name
    function.enable = True
    return function


class AzurLaneConfig(ConfigUpdater, ManualConfig, GeneratedConfig, ConfigWatcher):
    stop_event: threading.Event = None
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
        logger.attr("Server", self.SERVER)
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
        self.task: Function
        # Template config is used for dev tools
        self.is_template_config = config_name.startswith("template")

        if self.is_template_config:
            # For dev tools
            logger.info("Using template config, which is read only")
            self.auto_update = False
            self.task = name_to_function("template")
        else:
            self.load()
            if task is None:
                # Bind `Alas` by default which includes emulator settings.
                task = name_to_function("Alas")
            else:
                # Bind a specific task for debug purpose.
                task = name_to_function(task)
            self.bind(task)
            self.task = task
            self.save()

    def load(self):
        self.data = self.read_file(self.config_name)
        self.config_override()

        for path, value in self.modified.items():
            deep_set(self.data, keys=path, value=value)

    def bind(self, func, func_list=None):
        """
        Args:
            func (str, Function): Function to run
            func_list (set): Set of tasks to be bound
        """
        if func_list is None:
            func_list = ["Alas"]
        if isinstance(func, Function):
            func = func.command
        func_list.append(func)
        logger.info(f"Bind task {func_list}")

        # Bind arguments
        visited = set()
        self.bound.clear()
        for func in func_list:
            func_data = self.data.get(func, {})
            for group, group_data in func_data.items():
                for arg, value in group_data.items():
                    path = f"{group}.{arg}"
                    if path in visited:
                        continue
                    arg = path_to_arg(path)
                    super().__setattr__(arg, value)
                    self.bound[arg] = f"{func}.{path}"
                    visited.add(path)

        # Override arguments
        for arg, value in self.overridden.items():
            super().__setattr__(arg, value)

    @property
    def hoarding(self):
        minutes = int(
            deep_get(
                self.data, keys="Alas.Optimization.TaskHoardingDuration", default=0
            )
        )
        return timedelta(minutes=max(minutes, 0))

    @property
    def close_game(self):
        return deep_get(
            self.data, keys="Alas.Optimization.CloseGameDuringWait", default=False
        )

    @cached_property
    def stored(self) -> StoredGenerated:
        stored = StoredGenerated()
        # Bind config
        for _, value in iter_attribute(stored):
            value._bind(self)
            del_cached_property(value, '_stored')
        return stored

    def get_next_task(self):
        """
        Calculate tasks, set pending_task and waiting_task
        """
        pending = []
        waiting = []
        error = []
        now = datetime.now()
        if AzurLaneConfig.is_hoarding_task:
            now -= self.hoarding
        for func in self.data.values():
            func = Function(func)
            if not func.enable:
                continue
            if not isinstance(func.next_run, datetime):
                error.append(func)
            elif func.next_run < now:
                pending.append(func)
            else:
                waiting.append(func)

        f = Filter(regex=r"(.*)", attr=["command"])
        f.load(self.SCHEDULER_PRIORITY)
        if pending:
            pending = f.apply(pending)
        if waiting:
            waiting = f.apply(waiting)
            waiting = sorted(waiting, key=operator.attrgetter("next_run"))
        if error:
            pending = error + pending

        self.pending_task = pending
        self.waiting_task = waiting

    def get_next(self):
        """
        Returns:
            Function: Command to run
        """
        self.get_next_task()

        if self.pending_task:
            AzurLaneConfig.is_hoarding_task = False
            logger.info(f"Pending tasks: {[f.command for f in self.pending_task]}")
            task = self.pending_task[0]
            logger.attr("Task", task)
            return task
        else:
            AzurLaneConfig.is_hoarding_task = True

        if self.waiting_task:
            logger.info("No task pending")
            task = copy.deepcopy(self.waiting_task[0])
            task.next_run = (task.next_run + self.hoarding).replace(microsecond=0)
            logger.attr("Task", task)
            return task
        else:
            logger.critical("No task waiting or pending")
            logger.critical("Please enable at least one task")
            raise RequestHumanTakeover

    def save(self, mod_name='alas'):
        if not self.modified:
            return False

        for path, value in self.modified.items():
            deep_set(self.data, keys=path, value=value)

        logger.info(
            f"Save config {filepath_config(self.config_name, mod_name)}, {dict_to_kv(self.modified)}"
        )
        # Don't use self.modified = {}, that will create a new object.
        self.modified.clear()
        del_cached_property(self, 'stored')
        self.write_file(self.config_name, data=self.data)

    def update(self):
        self.load()
        self.config_override()
        self.bind(self.task)
        self.save()

    def config_override(self):
        now = datetime.now().replace(microsecond=0)
        limited = set()

        def limit_next_run(tasks, limit):
            for task in tasks:
                if task in limited:
                    continue
                limited.add(task)
                next_run = deep_get(
                    self.data, keys=f"{task}.Scheduler.NextRun", default=None
                )
                if isinstance(next_run, datetime) and next_run > limit:
                    deep_set(self.data, keys=f"{task}.Scheduler.NextRun", value=now)

        limit_next_run(['BattlePass'], limit=now + timedelta(days=31, seconds=-1))
        limit_next_run(self.args.keys(), limit=now + timedelta(hours=24, seconds=-1))

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
                record = arg.replace("Value", "Record")
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

    def cross_get(self, keys, default=None):
        """
        Get configs from other tasks.

        Args:
            keys (str, list[str]): Such as `{task}.Scheduler.Enable`
            default:

        Returns:
            Any:
        """
        return deep_get(self.data, keys=keys, default=default)

    def cross_set(self, keys, value):
        """
        Set configs to other tasks.

        Args:
            keys (str, list[str]): Such as `{task}.Scheduler.Enable`
            value (Any):

        Returns:
            Any:
        """
        self.modified[keys] = value
        if self.auto_update:
            self.update()

    def task_delay(self, success=None, server_update=None, target=None, minute=None, task=None):
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
            task (str):
                Set across task. None for current task.
        """

        def ensure_delta(delay):
            return timedelta(seconds=int(ensure_time(delay, precision=3) * 60))

        run = []
        if success is not None:
            interval = (
                120
                if success
                else 30
            )
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
                {
                    "success": success,
                    "server_update": server_update,
                    "target": target,
                    "minute": minute,
                },
                allow_none=False,
            )
            if task is None:
                task = self.task.command
            logger.info(f"Delay task `{task}` to {run} ({kv})")
            self.modified[f'{task}.Scheduler.NextRun'] = run
            self.update()
        else:
            raise ScriptError(
                "Missing argument in delay_next_run, should set at least one"
            )

    def task_call(self, task, force_call=True):
        """
        Call another task to run.

        That task will run when current task finished.
        But it might not be run because:
        - Other tasks should run first according to SCHEDULER_PRIORITY
        - Task is disabled by user

        Args:
            task (str): Task name to call, such as `Restart`
            force_call (bool):

        Returns:
            bool: If called.
        """
        if deep_get(self.data, keys=f"{task}.Scheduler.NextRun", default=None) is None:
            raise ScriptError(f"Task to call: `{task}` does not exist in user config")

        if force_call or self.is_task_enabled(task):
            logger.info(f"Task call: {task}")
            self.modified[f"{task}.Scheduler.NextRun"] = datetime.now().replace(
                microsecond=0
            )
            self.modified[f"{task}.Scheduler.Enable"] = True
            if self.auto_update:
                self.update()
            return True
        else:
            logger.info(f"Task call: {task} (skipped because disabled by user)")
            return False

    @staticmethod
    def task_stop(message=""):
        """
        Stop current task.

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
        # Update event
        if self.stop_event is not None:
            if self.stop_event.is_set():
                return True
        prev = self.task
        self.load()
        new = self.get_next()
        if prev == new:
            logger.info(f"Continue task `{new}`")
            return False
        else:
            logger.info(f"Switch task `{prev}` to `{new}`")
            return True

    def check_task_switch(self, message=""):
        """
        Stop current task when task switched.

        Raises:
            TaskEnd:
        """
        if self.task_switched():
            self.task_stop(message=message)

    def is_task_enabled(self, task):
        return bool(self.cross_get(keys=[task, 'Scheduler', 'Enable'], default=False))

    @property
    def DEVICE_SCREENSHOT_METHOD(self):
        return self.Emulator_ScreenshotMethod

    @property
    def DEVICE_CONTROL_METHOD(self):
        return self.Emulator_ControlMethod

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
        self.in_wrapper = False

    def __enter__(self):
        if self.main.auto_update:
            self.main.auto_update = False
        else:
            self.in_wrapper = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.in_wrapper:
            self.main.update()
            self.main.auto_update = True
