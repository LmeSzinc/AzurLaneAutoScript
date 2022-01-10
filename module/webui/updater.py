import builtins
import datetime
import subprocess
import threading
import time
from typing import Generator

import requests
from deploy.installer import DeployConfig, ExecutionError, Installer
from deploy.utils import DEPLOY_CONFIG, cached_property
from module.logger import logger
from module.webui.process_manager import AlasManager
from module.webui.utils import TaskHandler, get_next_time
from retry import retry


class Config(DeployConfig):
    def __init__(self, file=DEPLOY_CONFIG):
        self.file = file
        self.config = {}
        self.read()
        self.write()


class Updater(Config, Installer):
    def __init__(self, file=DEPLOY_CONFIG):
        super().__init__(file=file)
        self.state = 0
        self.delay = int(self.config['CheckUpdateInterval'])*60
        self.schedule_time = datetime.time.fromisoformat(
            self.config['AutoRestartTime'])
        self.event: threading.Event = None

    @cached_property
    def repo(self):
        return self.config['Repository']

    @cached_property
    def branch(self):
        return self.config['Branch']

    def _check_update(self) -> bool:
        self.state = 'checking'
        r = self.repo.split('/')
        owner = r[3]
        repo = r[4]
        if 'gitee' in r[2]:
            base = "https://gitee.com/api/v5/repos/"
            headers = {}
            token = self.config['ApiToken']
            if token:
                para = {"access_token": token}
        else:
            base = "https://api.github.com/repos/"
            headers = {
                'Accept': 'application/vnd.github.v3.sha'
            }
            para = {}
            token = self.config['ApiToken']
            if token:
                headers['Authorization'] = 'token ' + token

        p = subprocess.run(f"{self.git} rev-parse HEAD",
                           capture_output=True, text=True)
        if p.stdout is None:
            logger.warning("Cannot get local commit sha1")
            return 0

        local_sha = p.stdout

        if len(local_sha) != 41:
            logger.warning("Cannot get local commit sha1")
            return 0

        local_sha = local_sha.strip()

        try:
            list_commit = requests.get(
                base + f"{owner}/{repo}/branches/{self.branch}", headers=headers, params=para)
        except Exception as e:
            logger.exception(e)
            logger.warning("Check update failed")
            return 0

        if list_commit.status_code != 200:
            logger.warning(
                f"Check update failed, code {list_commit.status_code}")
            return 0
        try:
            sha = list_commit.json()['commit']['sha']
        except Exception as e:
            logger.exception(e)
            logger.warning("Check update failed when parsing return json")
            return 0

        if sha == local_sha:
            logger.info("No update")
            return 0

        try:
            get_commit = requests.get(
                base + f"{owner}/{repo}/commits/" + local_sha, headers=headers, params=para)
        except Exception as e:
            logger.exception(e)
            logger.warning("Check update failed")
            return 0

        if get_commit.status_code != 200:
            # for develops
            logger.info(
                f"Cannot find local commit {local_sha[:8]} in upstream, skip update")
            return 0

        logger.info(f"Update {sha[:8]} avaliable")
        return 1

    def check_update(self):
        if self.state in (0, 'failed'):
            self.state = updater._check_update()

    @retry(ExecutionError, tries=3, delay=10, logger=logger)
    def git_install(self):
        return super().git_install()

    @retry(ExecutionError, tries=3, delay=10, logger=logger)
    def pip_install(self):
        return super().pip_install()

    def update(self):
        logger.hr("Run update")
        backup, builtins.print = builtins.print, logger.info
        try:
            self.git_install()
            self.pip_install()
        except ExecutionError:
            logger.error("Update failed")
            builtins.print = backup
            return False
        builtins.print = backup
        return True

    def run_update(self):
        if self.state not in ('failed', 0, 1):
            return
        self._start_update()

    def _start_update(self):
        self.state = 'start'
        instances = AlasManager.running_instances()
        names = []
        for alas in instances:
            names.append(alas.config_name + '\n')

        logger.info("Waiting all running alas finish.")
        self._wait_update(instances, names)

    def _wait_update(self, instances, names):
        if self.state == 'cancel':
            self.state = 1
        self.state = 'wait'
        self.event.set()
        _instances = instances.copy()
        while _instances:
            for alas in _instances:
                if not alas.alive:
                    _instances.remove(alas)
                    logger.info(f"Alas [{alas.config_name}] stopped")
                    logger.info(
                        f"Remains: {[alas.config_name for alas in _instances]}")
            if self.state == 'cancel':
                self.state = 1
                AlasManager.start_alas(instances)
                return
            time.sleep(0.25)
        self._run_update(instances, names)

    def _run_update(self, instances, names):
        self.state = 'run update'
        logger.info("All alas stopped, start updating")

        if updater.update():
            self.state = 'reload'
            with open('./reloadalas', mode='w') as f:
                f.writelines(names)
            from module.webui.app import clearup
            clearup()
            time.sleep(1.25)
            self._trigger_reload()
        else:
            self.state = 'failed'
            logger.warning("Update failed")
            self.event.clear()
            AlasManager.start_alas(instances)
            return False
    
    @staticmethod
    def _trigger_reload():
        with open('./reloadflag', mode='w'):
            # app ended here and uvicorn will restart whole app
            pass

    def schedule_restart(self) -> Generator:
        th: TaskHandler
        th = yield
        if self.schedule_time is None:
            th.remove_current_task()
            yield
        th._task.delay = get_next_time(self.schedule_time)
        yield
        while True:
            if self.state == 0:
                self.state = updater._check_update()
            if self.state != 1:
                th._task.delay = get_next_time(self.schedule_time)
                yield
                continue

            if not self.run_update():
                self.state = 'failed'
            th._task.delay = get_next_time(self.schedule_time)
            yield

    def cancel(self):
        self.state = 'cancel'


updater = Updater()

if __name__ == '__main__':
    pass
    # if updater.check_update():
    updater.update()
