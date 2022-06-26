import datetime
import subprocess
import threading
import time
from typing import Generator, Tuple

import requests
from deploy.config import ExecutionError
from deploy.git import GitManager
from deploy.pip import PipManager
from deploy.utils import DEPLOY_CONFIG
from module.base.retry import retry
from module.logger import logger
from module.webui.config import DeployConfig
from module.webui.process_manager import ProcessManager
from module.webui.setting import State
from module.webui.utils import TaskHandler, get_next_time


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
        log = subprocess.run(
            command, capture_output=True, text=True, encoding="utf8", shell=True
        ).stdout
        return log

    def get_commit(self, revision="", n=1, short_sha1=False) -> Tuple:
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
        logs = list(map(lambda log: tuple(log.split("---")), logs))

        if n == 1:
            return logs[0]
        else:
            return logs

    def _check_update(self) -> bool:
        self.state = "checking"
        source = "origin"
        for _ in range(3):
            if self.execute(
                f'"{self.git}" fetch {source} {self.Branch}', allow_failure=True
            ):
                break
        else:
            logger.warning("Git fetch failed")
            return False

        log = self.execute_output(
            f'"{self.git}" log --not --remotes={source}/* -1 --oneline'
        )
        if log:
            logger.info(
                f"Cannot find local commit {log.split()[0]} in upstream, skip update"
            )
            return False

        sha1, _, _, message = self.get_commit(f"..{source}/{self.Branch}")

        if sha1:
            logger.info(f"New update available")
            logger.info(f"{sha1[:8]} - {message}")
            return True
        else:
            logger.info(f"No update")
            return False

    def _check_update_(self) -> bool:
        """
        Deprecated
        """
        self.state = "checking"
        r = self.Repository.split("/")
        owner = r[3]
        repo = r[4]
        if "gitee" in r[2]:
            base = "https://gitee.com/api/v5/repos/"
            headers = {}
            token = self.config["ApiToken"]
            if token:
                para = {"access_token": token}
        else:
            base = "https://api.github.com/repos/"
            headers = {"Accept": "application/vnd.github.v3.sha"}
            para = {}
            token = self.config["ApiToken"]
            if token:
                headers["Authorization"] = "token " + token

        try:
            list_commit = requests.get(
                base + f"{owner}/{repo}/branches/{self.Branch}",
                headers=headers,
                params=para,
            )
        except Exception as e:
            logger.exception(e)
            logger.warning("Check update failed")
            return 0

        if list_commit.status_code != 200:
            logger.warning(f"Check update failed, code {list_commit.status_code}")
            return 0
        try:
            sha = list_commit.json()["commit"]["sha"]
        except Exception as e:
            logger.exception(e)
            logger.warning("Check update failed when parsing return json")
            return 0

        local_sha, _, _, _ = self._get_local_commit()

        if sha == local_sha:
            logger.info("No update")
            return 0

        try:
            get_commit = requests.get(
                base + f"{owner}/{repo}/commits/" + local_sha,
                headers=headers,
                params=para,
            )
        except Exception as e:
            logger.exception(e)
            logger.warning("Check update failed")
            return 0

        if get_commit.status_code != 200:
            # for develops
            logger.info(
                f"Cannot find local commit {local_sha[:8]} in upstream, skip update"
            )
            return 0

        logger.info(f"Update {sha[:8]} available")
        return 1

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
        self.state = "start"
        instances = ProcessManager.running_instances()
        names = []
        for alas in instances:
            names.append(alas.config_name + "\n")

        logger.info("Waiting all running alas finish.")
        self._wait_update(instances, names)

    def _wait_update(self, instances, names):
        if self.state == "cancel":
            self.state = 1
        self.state = "wait"
        self.event.set()
        _instances = instances.copy()
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
        self._run_update(instances, names)

    def _run_update(self, instances, names):
        self.state = "run update"
        logger.info("All alas stopped, start updating")

        if self.update():
            if State.restart_event is not None:
                self.state = "reload"
                with open("./config/reloadalas", mode="w") as f:
                    f.writelines(names)
                from module.webui.app import clearup

                self._trigger_reload(2)
                clearup()
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

    def schedule_update(self) -> Generator:
        th: TaskHandler
        th = yield
        if self.schedule_time is None:
            th.remove_current_task()
            yield
        th._task.delay = get_next_time(self.schedule_time)
        yield
        while True:
            self.check_update()
            if self.state != 1:
                th._task.delay = get_next_time(self.schedule_time)
                yield
                continue
            if State.restart_event is None:
                yield
                continue
            if not self.run_update():
                self.state = "failed"
            th._task.delay = get_next_time(self.schedule_time)
            yield

    def cancel(self):
        self.state = "cancel"


updater = Updater()

if __name__ == "__main__":
    pass
    # if updater.check_update():
    updater.update()
