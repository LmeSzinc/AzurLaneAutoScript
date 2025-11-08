import os
import re
import shutil
import time
from threading import Lock

from deploy.config import DeployConfig
from module.logger import logger
from submodule.AlasFpyBridge.module.utils.headlessCliApplication import HeadlessCliApplication


class FGOpy(HeadlessCliApplication):
    def __init__(self, path, counter={}):
        # Caution that a mutable object is used for default paprameter
        assert os.path.isabs(path) and os.path.exists(path)
        launch = shutil.which("launch", path=path)
        assert launch
        # If you filled in `/usr/sbin` as the path, and there happened to be an executable named `launch`, and Alas had root privileges...
        halt = shutil.which("halt", path=path)
        os.environ["PATH"] = os.pathsep.join([
            os.path.abspath(os.path.dirname(DeployConfig().AdbExecutable)),
            os.environ["PATH"],
        ])
        self.counter = counter
        self.mutex = Lock()
        self.success = True
        self.last_error = ""
        self.tracebacking = False
        self.first_log = True
        self.log_pattern = re.compile(
            r"((?:FGO-py@.*?\(.*?\)> )*)"
            r"\[(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d,\d\d\d)\]"
            r"\[(DEBUG|INFO|WARNING|CRITICAL|ERROR)\]"
            r"<([a-zA-Z0-9_.]+?)> "
            r"(.*)"
        )
        super().__init__(launch)
        while self.first_log:
            time.sleep(0.5)
        self.start_orphan_slayer(self.info["PID"], halt)

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
            logger.info(f": {line}")
            return
        prompt, datetime, level, module, content = match.groups()
        getattr(logger, level.lower())(content)
        self.counter.get(content, lambda: None)()

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
