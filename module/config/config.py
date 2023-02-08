import copy
import datetime
import operator
import threading

import pywebio

from module.base.filter import Filter
from module.config.config_generated import GeneratedConfig
from module.config.config_manual import ManualConfig, OutputConfig
from module.config.config_updater import ConfigUpdater
from module.config.watcher import ConfigWatcher
from module.config.utils import *
from module.exception import RequestHumanTakeover, ScriptError
from module.logger import logger
from module.map.map_grids import SelectedGrids


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
        self.is_template_config = config_name == "template"

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

    def bind(self, func, func_set=None):
        """
        Args:
            func (str, Function): Function to run
            func_set (set): Set of tasks to be bound
        """
        if func_set is None:
            func_set = {"General", "Alas"}
        if isinstance(func, Function):
            func = func.command
        func_set.add(func)
        if func.startswith("Opsi"):
            func_set.add("OpsiGeneral")
        if (
            func.startswith("Event")
            or func.startswith("Raid")
            or func in ["MaritimeEscort", "GemsFarming"]
        ):
            func_set.add("EventGeneral")
            func_set.add("TaskBalancer")
        logger.info(f"Bind task {func_set}")

        # Bind arguments
        visited = set()
        self.bound.clear()
        for func in func_set:
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

        for task in ["Commission", "Research", "Reward"]:
            enable = deep_get(
                self.data, keys=f"{task}.Scheduler.Enable", default=None
            )
            if enable is not None and not enable:
                self.modified[f"{task}.Scheduler.Enable"] = True
        force_enable = list

        force_enable(
            [
                "Commission",
                "Research",
                "Reward",
            ]
        )
        limit_next_run(["Commission", "Reward"], limit=now + timedelta(hours=12, seconds=-1))
        limit_next_run(["Research"], limit=now + timedelta(hours=24, seconds=-1))
        limit_next_run(["OpsiExplore", "OpsiCrossMonth", "OpsiVoucher", "OpsiMonthBoss"],
                       limit=now + timedelta(days=31, seconds=-1))
        limit_next_run(["OpsiArchive"], limit=now + timedelta(days=7, seconds=-1))
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
                self.Scheduler_SuccessInterval
                if success
                else self.Scheduler_FailureInterval
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

    def opsi_task_delay(self, recon_scan=False, submarine_call=False, ap_limit=False, cl1_preserve=False):
        """
        Delay the NextRun of all OpSi tasks.

        Args:
            recon_scan (bool): True to delay all tasks requiring recon scan 27 min.
            submarine_call (bool): True to delay all tasks requiring submarine call 60 min.
            ap_limit (bool): True to delay all tasks requiring action points 360 min.
            cl1_preserve (bool): True to delay tasks requiring massive action points 360 min.
        """
        if not recon_scan and not submarine_call and not ap_limit and not cl1_preserve:
            return None
        kv = dict_to_kv(
            {
                "recon_scan": recon_scan,
                "submarine_call": submarine_call,
                "ap_limit": ap_limit,
                "cl1_preserve": cl1_preserve,
            }
        )

        def delay_tasks(task_list, minutes):
            next_run = datetime.now().replace(microsecond=0) + timedelta(
                minutes=minutes
            )
            for task in task_list:
                keys = f"{task}.Scheduler.NextRun"
                current = deep_get(self.data, keys=keys, default=DEFAULT_TIME)
                if current < next_run:
                    logger.info(f"Delay task `{task}` to {next_run} ({kv})")
                    self.modified[keys] = next_run

        def is_submarine_call(task):
            return (
                deep_get(self.data, keys=f"{task}.OpsiFleet.Submarine", default=False)
                or "submarine"
                in deep_get(
                    self.data, keys=f"{task}.OpsiFleetFilter.Filter", default=""
                ).lower()
            )

        def is_force_run(task):
            return (
                deep_get(self.data, keys=f"{task}.OpsiExplore.ForceRun", default=False)
                or deep_get(
                    self.data, keys=f"{task}.OpsiObscure.ForceRun", default=False
                )
                or deep_get(
                    self.data, keys=f"{task}.OpsiAbyssal.ForceRun", default=False
                )
                or deep_get(
                    self.data, keys=f"{task}.OpsiStronghold.ForceRun", default=False
                )
            )

        def is_special_radar(task):
            return deep_get(
                self.data, keys=f"{task}.OpsiExplore.SpecialRadar", default=False
            )

        if recon_scan:
            tasks = SelectedGrids(["OpsiExplore", "OpsiObscure", "OpsiStronghold"])
            tasks = tasks.delete(tasks.filter(is_force_run)).delete(
                tasks.filter(is_special_radar)
            )
            delay_tasks(tasks, minutes=27)
        if submarine_call:
            tasks = SelectedGrids(
                [
                    "OpsiExplore",
                    "OpsiDaily",
                    "OpsiObscure",
                    "OpsiAbyssal",
                    "OpsiArchive",
                    "OpsiStronghold",
                    "OpsiMeowfficerFarming",
                    "OpsiMonthBoss",
                ]
            )
            tasks = tasks.filter(is_submarine_call).delete(tasks.filter(is_force_run))
            delay_tasks(tasks, minutes=60)
        if ap_limit:
            tasks = SelectedGrids(
                [
                    "OpsiExplore",
                    "OpsiDaily",
                    "OpsiObscure",
                    "OpsiAbyssal",
                    "OpsiStronghold",
                    "OpsiMeowfficerFarming",
                ]
            )
            if get_os_reset_remain() > 0:
                delay_tasks(tasks, minutes=360)
            else:
                logger.info("Just less than 1 day to OpSi reset, delay 2.5 hours")
                delay_tasks(tasks, minutes=150)
        if cl1_preserve:
            tasks = SelectedGrids(
                [
                    "OpsiObscure",
                    "OpsiAbyssal",
                    "OpsiStronghold",
                    "OpsiMeowfficerFarming",
                ]
            )
            delay_tasks(tasks, minutes=360)

        self.update()

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

        if force_call or deep_get(
            self.data, keys=f"{task}.Scheduler.Enable", default=False
        ):
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

    @property
    def campaign_name(self):
        """
        Sub-directory name when saving drop record.
        """
        name = self.Campaign_Name.lower().replace("-", "_")
        if name[0].isdigit():
            name = "campaign_" + str(name)
        if self.Campaign_Mode == "hard":
            name += "_hard"
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
            if attr.endswith("__"):
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
            if self.Fleet_FleetOrder in [
                "fleet1_mob_fleet2_boss",
                "fleet1_boss_fleet2_mob",
            ]:
                return 2
            else:
                return 1
        else:
            return 1

    @FLEET_BOSS.setter
    def FLEET_BOSS(self, value):
        self._fleet_boss = value

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


pywebio.output.Output = OutputConfig
pywebio.pin.Output = OutputConfig


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
