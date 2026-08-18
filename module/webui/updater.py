import datetime
import subprocess
import threading
import time

from deploy.config import ExecutionError
from deploy.git import GitManager
from deploy.pip import PipManager
from deploy.utils import DEPLOY_CONFIG
from module.base.retry import retry
from module.logger import logger
from module.webui.config import DeployConfig
from module.webui.process_manager import ProcessManager
from module.webui.setting import State


class Updater(DeployConfig, GitManager, PipManager):
    def __init__(self, file=DEPLOY_CONFIG):
        super().__init__(file=file)
        self.state = 0
        self.event: threading.Event = None

    @property
    def delay(self):
        self.read()
        return int(self.CheckUpdateInterval) * 60

    @property
    def schedule_time(self):
        self.read()
        t = self.AutoRestartTime
        if t is not None:
            return datetime.time.fromisoformat(t)
        else:
            return None

    def execute_output(self, command) -> str:
        command = command.replace(r"\\", "/").replace("\\", "/").replace('"', '"')
        log = subprocess.run(command, capture_output=True, text=True, encoding="utf8", shell=True).stdout
        return log

    def get_commit(self, revision="", n=1, short_sha1=False) -> tuple:
        """
        Return:
            (sha1, author, isotime, message,)
        """
        ph = "h" if short_sha1 else "H"

        log = self.execute_output(
            f'"{self.git}" log {revision} --pretty=format:"%{ph}---%an---%ad---%s" --date=iso -{n}'
        )

        if not log:
            return None, None, None, None

        logs = log.split("\n")
        logs = [tuple(log.split("---")) for log in logs]

        if n == 1:
            return logs[0]
        else:
            return logs

    def _check_update(self) -> bool:
        self.state = "checking"

        source = "origin"
        for _ in range(3):
            if self.execute(f'"{self.git}" fetch {source} {self.Branch}', allow_failure=True):
                break
        else:
            logger.warning("Git fetch failed")
            return False

        log = self.execute_output(f'"{self.git}" log --not --remotes={source}/* -1 --oneline')
        if log:
            logger.info(f"Cannot find local commit {log.split()[0]} in upstream, skip update")
            return False

        sha1, _, _, message = self.get_commit(f"..{source}/{self.Branch}")

        if sha1:
            logger.info("New update available")
            logger.info(f"{sha1[:8]} - {message}")
            return True
        else:
            logger.info("No update")
            return False

    def check_update(self):
        if self.state in (0, "failed", "finish"):
            self.state = self._check_update()

    @retry(ExecutionError, tries=3, delay=5, logger=None)
    def git_install(self):
        return super().git_install()

    @retry(ExecutionError, tries=3, delay=5, logger=None)
    def pip_install(self):
        return super().pip_install()

    def update(self):
        logger.hr("Run update")
        try:
            self.git_install()
            self.pip_install()
        except ExecutionError:
            return False
        return True

    def run_update(self):
        if self.state not in ("failed", 0, 1):
            return
        self._start_update()

    def _start_update(self):
        # The event is normally created in _startup, but a manual
        # /update/run can arrive before that thread runs.
        if self.event is None:
            self.event = State.manager.Event()
        self.state = "start"
        instances = ProcessManager.running_instances()
        names = []
        for alas in instances:
            names.append(alas.config_name + "\n")

        logger.info("Waiting all running alas finish.")
        self._wait_update(instances, names)

    def _wait_update(self, instances: list[ProcessManager], names):
        if self.state == "cancel":
            self.state = 1
        self.state = "wait"
        self.event.set()
        _instances = instances.copy()
        start_time = time.time()
        while _instances:
            for alas in _instances:
                if not alas.alive:
                    _instances.remove(alas)
                    logger.info(f"Alas [{alas.config_name}] stopped")
                    logger.info(f"Remains: {[alas.config_name for alas in _instances]}")
            if self.state == "cancel":
                self.state = 1
                self.event.clear()
                ProcessManager.restart_processes(instances, self.event)
                return
            time.sleep(0.25)
            if time.time() - start_time > 60 * 10:
                logger.warning("Waiting alas shutdown timeout, force kill")
                for alas in _instances:
                    alas.stop()
                break
        self._run_update(instances, names)

    def _run_update(self, instances, names):
        self.state = "run update"
        logger.info("All alas stopped, start updating")

        if self.update():
            if State.restart_event is not None:
                self.state = "reload"
                with open("./config/reloadalas", mode="w") as f:
                    f.writelines(names)
                self._trigger_reload(2)
                State.clearup()
            else:
                self.state = "finish"
        else:
            self.state = "failed"
            logger.warning("Update failed")
            self.event.clear()
            ProcessManager.restart_processes(instances, self.event)
            return False

    @staticmethod
    def _trigger_reload(delay=2):
        def trigger():
            # with open("./config/reloadflag", mode="w"):
            #     # app ended here and uvicorn will restart whole app
            #     pass
            State.restart_event.set()

        timer = threading.Timer(delay, trigger)
        timer.start()


updater = Updater()

if __name__ == "__main__":
    pass
    # if updater.check_update():
    updater.update()
