import re
import time
from threading import Lock

from module.logger import logger
from submodule.AlasFpyBridge.module.utils.headlessCliApplication import HeadlessCliApplication


class FGOpy(HeadlessCliApplication):
    def __init__(self, cmd):
        super().__init__(cmd)
        self.mutex = Lock()
        self.success = True
        self.last_error = ""
        self.tracebacking = False
        self.log_pattern = re.compile(
            r"((?:FGO-py@.*?\(.*?\)> )?)\[(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d,\d\d\d)\]\[(DEBUG|INFO|WARNING|CRITICAL|ERROR)\]<([a-zA-Z0-9_.]+?)> (.*)"
        )

    def callback(self, line):
        if line == "exited":
            self.last_error = "exited"
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
        head, datetime, level, module, content = match.groups()
        getattr(logger, level.lower())(content)
    
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
