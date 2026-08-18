import os
import re
import threading
import time
from datetime import datetime

import cv2

# The automation loop runs many small image ops (screenshot, template
# matching, preprocessing). OpenCV's default thread pool (one per core)
# creates a thread storm on many-core machines and contends with the
# desktop; a small pool is faster and keeps the system smooth.
cv2.setNumThreads(2)

from module.base.decorator import cached_property
from module.config.config import AzurLaneConfig
from module.exception import RequestHumanTakeover
from module.logger import logger
from module.scheduler.scheduler import Scheduler
from module.scheduler.task_record import TaskRecord


class AzurLaneAutoScript(Scheduler):
    """Alas app shell: config/device/checker, task dispatch, and infra methods.

    The scheduler loop lives in the `Scheduler` mixin (module/scheduler).
    """

    stop_event: threading.Event | None = None

    def __init__(self, config_name="alas"):
        logger.hr("Start", level=0)
        self.config_name = config_name
        # Skip first restart
        self.is_first_task = True
        # Consecutive failure counts, see module.scheduler.task_record
        self.task_record = TaskRecord()

    @cached_property
    def config(self):
        try:
            config = AzurLaneConfig(config_name=self.config_name)
            return config
        except RequestHumanTakeover:
            logger.critical("Request human takeover")
            exit(1)
        except Exception as e:
            logger.exception(e)
            exit(1)

    @cached_property
    def device(self):
        try:
            from module.device.device import Device

            device = Device(config=self.config)
            return device
        except RequestHumanTakeover:
            logger.critical("Request human takeover")
            exit(1)
        except Exception as e:
            logger.exception(e)
            exit(1)

    @cached_property
    def checker(self):
        try:
            from module.server_checker import ServerChecker

            checker = ServerChecker(server=self.config.Emulator_ServerName)
            return checker
        except Exception as e:
            logger.exception(e)
            exit(1)

    def _resolve_task(self, command):
        """
        Resolve a task command (snake_case method name or registered task)
        to a zero-arg callable. Registered tasks come from the declarative
        TASK_REGISTRY; infra commands (restart/start/goto_main) fall back to
        method lookup for backward compatibility.
        """
        from module.tasks.registry import TASK_BY_COMMAND, TASK_REGISTRY

        # command is the inflection.underscore() form, e.g. "opsi_explore";
        # TASK_BY_COMMAND maps it back to the PascalCase task name.
        task_name = TASK_BY_COMMAND.get(command)
        entry = TASK_REGISTRY.get(task_name) if task_name is not None else None
        if entry is not None:
            import importlib

            module = importlib.import_module(entry.module)
            if entry.function is not None:
                function = entry.function
                return lambda: getattr(module, function)(config=self.config)

            assert entry.class_name is not None
            task_class = getattr(module, entry.class_name)
            kwargs = entry.kwargs(self.config) if callable(entry.kwargs) else (entry.kwargs or {})
            if entry.task_arg:
                kwargs = {**kwargs, "task": task_name}
            instance = task_class(config=self.config, device=self.device, **kwargs)
            method = entry.method
            assert method is not None
            method_kwargs = (
                entry.method_kwargs(self.config)
                if callable(entry.method_kwargs)
                else (entry.method_kwargs or {})
            )
            return lambda: getattr(instance, method)(**method_kwargs)

        # Fallback: infra methods (restart/start/goto_main) and any legacy method
        return self.__getattribute__(command)

    def save_error_log(self):
        """
        Save last 60 screenshots in ./log/error/<timestamp>
        Save logs to ./log/error/<timestamp>/log.txt
        """
        from module.base.utils import save_image
        from module.handler.sensitive_info import handle_sensitive_image, handle_sensitive_logs

        if self.config.Error_SaveError:
            if not os.path.exists("./log/error"):
                os.mkdir("./log/error")
            folder = f"./log/error/{int(time.time() * 1000)}"
            logger.warning(f"Saving error: {folder}")
            os.mkdir(folder)
            for data in self.device.screenshot_deque:
                image_time = datetime.strftime(data["time"], "%Y-%m-%d_%H-%M-%S-%f")
                image = handle_sensitive_image(data["image"])
                save_image(image, f"{folder}/{image_time}.png")
            with open(logger.log_file, encoding="utf-8") as f:
                lines = f.readlines()
                start = 0
                for index, line in enumerate(lines):
                    line = line.strip(" \r\t\n")
                    if re.match("^═{15,}$", line):
                        start = index
                lines = lines[start - 2 :]
                lines = handle_sensitive_logs(lines)
            with open(f"{folder}/log.txt", "w", encoding="utf-8") as f:
                f.writelines(lines)

    def restart(self):
        from module.handler.login import LoginHandler

        LoginHandler(self.config, device=self.device).app_restart()

    def start(self):
        from module.handler.login import LoginHandler

        LoginHandler(self.config, device=self.device).app_start()

    def goto_main(self):
        from module.handler.login import LoginHandler
        from module.ui.ui import UI

        if self.device.app_is_running():
            logger.info("App is already running, goto main page")
            UI(self.config, device=self.device).ui_goto_main()
        else:
            logger.info("App is not running, start app and goto main page")
            LoginHandler(self.config, device=self.device).app_start()
            UI(self.config, device=self.device).ui_goto_main()


if __name__ == "__main__":
    alas = AzurLaneAutoScript()
    alas.loop()
