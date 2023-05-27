import os
import platform
import re
import time
from threading import Lock

from module.logger import logger
from submodule.AlasFpyBridge.module.utils.headlessCliApplication import HeadlessCliApplication


class FGOpy(HeadlessCliApplication):
    def __init__(self, path):
        ext = {
            "Windows": "bat",
            "Linux": "sh",
        }.get(platform.system(), "")
        launch = os.path.join(path, f"launch.{ext}")
        assert os.path.exists(launch)
        halt = os.path.join(path, f"halt.{ext}")
        if not os.path.exists(halt):
            halt = ""
        self.mutex = Lock()
        self.success = True
        self.last_error = ""
        self.tracebacking = False
        self.first_log = True
        self.log_pattern = re.compile(
            r"((?:FGO-py@.*?\(.*?\)> )*)\[(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d,\d\d\d)\]\[(DEBUG|INFO|WARNING|CRITICAL|ERROR)\]<([a-zA-Z0-9_.]+?)> (.*)"
        )
        super().__init__(launch)
        while self.first_log:
            time.sleep(.5)
        self.reg_halt(self.info["PID"], halt)

    def callback(self, line):
        if line == "exited":
            self.last_error = "exited"
            if self.mutex.locked():
                self.mutex.release()
            return
        if line.startswith("Traceback"):
            self.success = False
            self.tracebacking = True
            logger.error(line)
            return
        if self.tracebacking:
            logger.error(line)
            if not line.startswith(" "):
                self.last_error = line
                self.tracebacking = False
            return

        match = self.log_pattern.fullmatch(line)
        if match is None:
            logger.info(f"... {line}")
            return
        prompt, datetime, level, module, content = match.groups()
        getattr(logger, level.lower())(content)

        if self.first_log:
            self.first_log = False
            self.info = (lambda x: dict(zip(x, x)))(iter(content.split()))
            return

        if level == "CRITICAL":
            self.last_error = content
            return

        if content.startswith("Done in"):
            self.mutex.release()

    def run(self, cmd):
        self.mutex.acquire()
        self.success = True
        self.last_error = ""
        self.feed(cmd)
        with self.mutex:
            pass
        if self.last_error == "exited":
            exit(not self.success)
        return self.success
