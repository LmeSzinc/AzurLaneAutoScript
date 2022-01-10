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
    @cached_property
    def repo(self):
        return self.config['Repository']

    @cached_property
    def branch(self):
        return self.config['Branch']

    def check_update(self) -> bool:
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
            return False

        local_sha = p.stdout

        if len(local_sha) != 41:
            logger.warning("Cannot get local commit sha1")
            return False

        local_sha = local_sha.strip()

        try:
            list_commit = requests.get(
                base + f"{owner}/{repo}/branches/{self.branch}", headers=headers, params=para)
        except Exception as e:
            logger.exception(e)
            logger.warning("Check update failed")
            return False

        if list_commit.status_code != 200:
            logger.warning(
                f"Check update failed, code {list_commit.status_code}")
            return False
        try:
            sha = list_commit.json()['commit']['sha']
        except Exception as e:
            logger.exception(e)
            logger.warning("Check update failed when parsing return json")
            return False

        if sha == local_sha:
            logger.info("No update")
            return False

        try:
            get_commit = requests.get(
                base + f"{owner}/{repo}/commits/" + local_sha, headers=headers, params=para)
        except Exception as e:
            logger.exception(e)
            logger.warning("Check update failed")
            return False

        if get_commit.status_code != 200:
            # for develops
            logger.info(
                f"Cannot find local commit {local_sha[:8]} in upstream, skip update")
            return False

        logger.info(f"Update {sha[:8]} avaliable")
        return True

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


have_update = False
updater = Updater()
delay = int(updater.config['CheckUpdateInterval'])*60
schedule_time = datetime.time.fromisoformat(
    updater.config['AutoRestartTime'])
event: threading.Event = None


def update_state() -> Generator:
    global have_update
    yield
    while True:
        if not have_update:
            have_update = updater.check_update()
        yield


def update():
    if event.is_set():
        return
    instances = AlasManager.running_instances()
    names = []
    for alas in instances:
        names.append(alas.config_name + '\n')

    _instances = instances.copy()
    logger.info("Waiting all running alas finish.")
    event.set()
    while _instances:
        for alas in _instances:
            if not alas.alive:
                _instances.remove(alas)
                logger.info(f"Alas [{alas.config_name}] stopped")
                logger.info(
                    f"Remains: {[alas.config_name for alas in _instances]}")
        time.sleep(0.25)

    logger.info("All alas stopped, start updating")

    if updater.update():
        from module.webui.app import clearup
        clearup()
        with open('./reloadalas', mode='w') as f:
            f.writelines(names)
        with open('./reloadflag', mode='w'):
            pass
        # program ended here and uvicorn will restart whole app
    else:
        logger.warning("Update failed")
        event.clear()
        AlasManager.start_alas(instances)
        return False


def schedule_restart() -> Generator:
    th: TaskHandler
    th = yield
    if schedule_time is None:
        th.remove_current_task()
        yield
    th._task.delay = get_next_time(schedule_time)
    yield
    while True:
        if not have_update:
            have_update = updater.check_update()
        if not have_update:
            th._task.delay = get_next_time(schedule_time)
            yield
            continue

        update()
        th._task.delay = get_next_time(schedule_time)
        yield


if __name__ == '__main__':
    pass
    # if updater.check_update():
    updater.update()
