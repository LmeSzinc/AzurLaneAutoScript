"""Alas scheduler: task execution policy, waiting, and the main scheduler loop.

Extracted from alas.py (P2.3 refactor), completing the scheduler split that
started with TaskRecord (module/scheduler/task_record.py). `Scheduler` is a
mixin: `alas.AzurLaneAutoScript` inherits it and provides the app shell
surface the loop drives — the `config` / `device` / `checker` cached
properties, `save_error_log()`, `_resolve_task()`, the `restart` / `start` /
`goto_main` infra methods, plus `task_record`, `is_first_task` and
`stop_event`. All references are late-bound against the concrete shell, so
subclasses (e.g. submodule bridge scripts) keep working unchanged.

Mirrors Alasio's `AlasioScheduler`, which decomposes the same loop into
`_task_loop` / `_run_task` / `_wait_future`; here the methods keep their
legacy names (`run` / `wait_until` / `get_next_task` / `loop`) so the bodies
move verbatim.

Semantics kept identical to the legacy alas.py implementation; the moved
method bodies are byte-for-byte the same code (verified against the
pre-refactor snapshot).
"""

from __future__ import annotations

import threading
import time
import typing as t
from datetime import datetime, timedelta

import inflection

from module.base.decorator import del_cached_property
from module.config.config import AzurLaneConfig, TaskEnd
from module.exception import (
    GameBugError,
    GameNotRunningError,
    GamePageUnknownError,
    GameStuckError,
    GameTooManyClickError,
    RequestHumanTakeover,
    ScriptError,
)
from module.logger import logger
from module.notify import handle_notify
from module.scheduler.task_record import TaskRecord

if t.TYPE_CHECKING:
    from module.device.base import DeviceBase
    from module.server_checker import ServerChecker


class Scheduler:
    # --- shell surface provided by alas.AzurLaneAutoScript -----------------
    # Declared annotation-only (no values, no runtime attributes) so type
    # checkers can verify this mixin body against the contract the concrete
    # shell fulfills. Mirrors the DeviceBase protocol approach in
    # module/device/base.py; hasattr()-based structure checks still resolve
    # against the real shell, so a missing implementation is still caught.
    config_name: str
    config: AzurLaneConfig
    device: DeviceBase
    checker: ServerChecker
    stop_event: threading.Event | None
    task_record: TaskRecord
    is_first_task: bool
    _resolve_task: t.Callable[[str], t.Callable[[], object]]
    save_error_log: t.Callable[[], None]

    def run(self, command, skip_first_screenshot=False):
        # Bind the task name to every record logged during execution so
        # logs can be filtered per task (loguru contextualize, L3).
        with logger.contextualize(task=command):  # type: ignore[attr-defined] (loguru ships no py.typed)
            return self._run(command, skip_first_screenshot)

    def _run(self, command, skip_first_screenshot=False):
        try:
            if not skip_first_screenshot:
                self.device.screenshot()
            func = self._resolve_task(command)
            func()
            return True
        except TaskEnd:
            return True
        except GameNotRunningError as e:
            logger.warning(e)
            self.config.task_call("Restart")
            return False
        except (GameStuckError, GameTooManyClickError) as e:
            logger.error(e)
            self.save_error_log()
            logger.warning(f"Game stuck, {self.device.package} will be restarted in 10 seconds")
            logger.warning("If you are playing by hand, please stop Alas")
            self.config.task_call("Restart")
            self.device.sleep(10)
            return False
        except GameBugError as e:
            logger.warning(e)
            self.save_error_log()
            logger.warning("An error has occurred in Azur Lane game client, Alas is unable to handle")
            logger.warning(f"Restarting {self.device.package} to fix it")
            self.config.task_call("Restart")
            self.device.sleep(10)
            return False
        except GamePageUnknownError:
            logger.info("Game server may be under maintenance or network may be broken, check server status now")
            self.checker.check_now()
            if self.checker.is_available():
                logger.critical("Game page unknown")
                self.save_error_log()
                handle_notify(
                    self.config.Error_OnePushConfig,
                    title=f"Alas <{self.config_name}> crashed",
                    content=f"<{self.config_name}> GamePageUnknownError",
                )
                exit(1)
            else:
                self.checker.wait_until_available()
                return False
        except ScriptError as e:
            logger.exception(e)
            logger.critical("This is likely to be a mistake of developers, but sometimes just random issues")
            handle_notify(
                self.config.Error_OnePushConfig,
                title=f"Alas <{self.config_name}> crashed",
                content=f"<{self.config_name}> ScriptError",
            )
            exit(1)
        except RequestHumanTakeover:
            logger.critical("Request human takeover")
            handle_notify(
                self.config.Error_OnePushConfig,
                title=f"Alas <{self.config_name}> crashed",
                content=f"<{self.config_name}> RequestHumanTakeover",
            )
            exit(1)
        except Exception as e:
            logger.exception(e)
            self.save_error_log()
            handle_notify(
                self.config.Error_OnePushConfig,
                title=f"Alas <{self.config_name}> crashed",
                content=f"<{self.config_name}> Exception occured",
            )
            exit(1)

    def wait_until(self, future):
        """
        Wait until a specific time.

        Args:
            future (datetime):

        Returns:
            bool: True if wait finished, False if config changed.
        """
        future = future + timedelta(seconds=1)
        self.config.start_watching()
        while 1:
            if datetime.now() > future:
                return True
            if self.stop_event is not None:
                if self.stop_event.is_set():
                    logger.info("Update event detected")
                    logger.info(f"[{self.config_name}] exited. Reason: Update")
                    exit(0)

            time.sleep(5)

            if self.config.should_reload():
                return False

    def get_next_task(self):
        """
        Returns:
            str: Name of the next task.
        """
        while 1:
            task = self.config.get_next()
            self.config.task = task
            self.config.bind(task)

            from module.base.resource import release_resources

            if self.config.task.command != "Alas":
                release_resources(next_task=task.command)

            if task.next_run > datetime.now():
                logger.info(f"Wait until {task.next_run} for task `{task.command}`")
                self.is_first_task = False
                method = self.config.Optimization_WhenTaskQueueEmpty
                if method == "close_game":
                    logger.info("Close game during wait")
                    self.device.app_stop()
                    release_resources()
                    self.device.release_during_wait()
                    if not self.wait_until(task.next_run):
                        del_cached_property(self, "config")
                        continue
                    if task.command != "Restart":
                        self.config.task_call("Restart")
                        del_cached_property(self, "config")
                        continue
                elif method == "goto_main":
                    logger.info("Goto main page during wait")
                    self.run("goto_main")
                    release_resources()
                    self.device.release_during_wait()
                    if not self.wait_until(task.next_run):
                        del_cached_property(self, "config")
                        continue
                elif method == "stay_there":
                    logger.info("Stay there during wait")
                    release_resources()
                    self.device.release_during_wait()
                    if not self.wait_until(task.next_run):
                        del_cached_property(self, "config")
                        continue
                else:
                    logger.warning(f"Invalid Optimization_WhenTaskQueueEmpty: {method}, fallback to stay_there")
                    release_resources()
                    self.device.release_during_wait()
                    if not self.wait_until(task.next_run):
                        del_cached_property(self, "config")
                        continue
            break

        AzurLaneConfig.is_hoarding_task = False
        return task.command

    def loop(self):
        logger.set_file_logger(self.config_name)
        logger.info(f"Start scheduler loop: {self.config_name}")

        while 1:
            # Check update event from GUI
            if self.stop_event is not None:
                if self.stop_event.is_set():
                    logger.info("Update event detected")
                    logger.info(f"Alas [{self.config_name}] exited.")
                    break
            # Check game server maintenance
            self.checker.wait_until_available()
            if self.checker.is_recovered():
                # There is an accidental bug hard to reproduce
                # Sometimes, config won't be updated due to blocking
                # even though it has been changed
                # So update it once recovered
                del_cached_property(self, "config")
                logger.info("Server or network is recovered. Restart game client")
                self.config.task_call("Restart")
            # Get task
            task = self.get_next_task()
            # Init device and change server
            _ = self.device
            self.device.config = self.config
            # Skip first restart
            if self.is_first_task and task == "Restart":
                logger.info("Skip task `Restart` at scheduler start")
                self.config.task_delay(server_update=True)
                del_cached_property(self, "config")
                continue

            # Run
            logger.info(f"Scheduler: Start task `{task}`")
            # Tell the webui what is actually running right now (get_next()
            # publishes before the wait; hoarded tasks start after it).
            self.config.publish_scheduler_state(current=task)
            self.device.stuck_record_clear()
            self.device.click_record_clear()
            logger.hr(task, level=0)
            success = self.run(inflection.underscore(task))
            logger.info(f"Scheduler: End task `{task}`")
            self.is_first_task = False

            # Check failures
            self.task_record.mark_result(task, success=success)
            if self.task_record.too_many_failures(task, limit=3):
                logger.critical(f"Task `{task}` failed 3 or more times.")
                logger.critical(
                    "Possible reason #1: You haven't used it correctly. Please read the help text of the options."
                )
                logger.critical(
                    "Possible reason #2: There is a problem with this task. "
                    "Please contact developers or try to fix it yourself."
                )
                logger.critical("Request human takeover")
                handle_notify(
                    self.config.Error_OnePushConfig,
                    title=f"Alas <{self.config_name}> crashed",
                    content=f"<{self.config_name}> RequestHumanTakeover\nTask `{task}` failed 3 or more times.",
                )
                exit(1)

            if success:
                del_cached_property(self, "config")
                continue
            elif self.config.Error_HandleError:
                # self.config.task_delay(success=False)
                del_cached_property(self, "config")
                self.checker.check_now()
                continue
            else:
                break
