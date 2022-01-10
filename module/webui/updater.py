import datetime
import os
import subprocess
import threading
import time
from typing import Generator

import requests
from deploy.installer import DeployConfig
from deploy.installer import PipManager as Pip
from deploy.installer import cached_property, urlparse
from deploy.utils import DEPLOY_CONFIG
from module.logger import logger
from module.webui.process_manager import AlasManager
from module.webui.utils import TaskHandler, get_next_time


class Config(DeployConfig):
    def __init__(self, file=DEPLOY_CONFIG):
        self.file = file
        self.config = {}
        self.read()
        self.write()

    def execute(self, command: str):
        command = command.replace(
            r'\\', '/').replace('\\', '/').replace('\"', '"')
        error_code = os.system(command)
        if error_code:
            logger.warning(
                f"command '{command}' failed, error_code: {error_code}")
            return False
        else:
            return True


class GitManager(Config):
    @cached_property
    def git(self):
        return self.filepath('GitExecutable')

    @cached_property
    def repo(self):
        return self.config['Repository']

    @cached_property
    def branch(self):
        return self.config['Branch']

    @cached_property
    def proxy(self):
        return self.config['GitProxy']

    @cached_property
    def keep_changes(self):
        return self.bool('KeepLocalChanges')

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

    def update(self):
        source = 'origin'
        if self.keep_changes:
            if not self.execute(f'"{self.git}" stash'):
                logger.warning(
                    'Stash failed, this may be the first installation, drop changes instead')
                self.execute(
                    f'"{self.git}" reset --hard {source}/{self.branch}')
        else:
            self.execute(f'"{self.git}" reset --hard {source}/{self.branch}')

        if not self.execute(f'"{self.git}" pull --ff-only {source} {self.branch}'):
            logger.warning("Git pull failed")
            return False

        if self.keep_changes:
            if self.execute(f'"{self.git}" stash pop'):
                pass
            else:
                # No local changes to existing files, untracked files not included
                logger.warning(
                    'Stash pop failed, there seems to be no local changes, skip instead')

        return True


class PipManager(Config, Pip):
    def update(self):
        if not self.bool('InstallDependencies'):
            print('InstallDependencies is disabled, skip')
            return True

        arg = []
        if self.bool('PypiMirror'):
            mirror = self.config['PypiMirror']
            arg += ['-i', mirror]
            # Trust http mirror
            if 'http:' in mirror:
                arg += ['--trusted-host', urlparse(mirror).hostname]

        # Don't update pip, just leave it.
        # hr1('Update pip')
        # self.execute(f'"{self.pip}" install --upgrade pip{arg}')
        arg += ['--disable-pip-version-check']
        arg = ' ' + ' '.join(arg) if arg else ''
        if self.execute(f'"{self.pip}" install -r requirements.txt{arg}'):
            return True


have_update = False
git_manager = GitManager()
pip_manager = PipManager()
delay = int(git_manager.config['CheckUpdateInterval'])*60
schedule_time = datetime.time.fromisoformat(
    git_manager.config['AutoRestartTime'])
event: threading.Event = None


def update_state() -> Generator:
    global have_update
    yield
    while True:
        if not have_update:
            have_update = git_manager.check_update()
        yield


def run_update():
    logger.hr("Run update")
    # time.sleep(5)
    # return True
    for _ in range(3):
        if git_manager.update():
            break
    else:
        logger.warning("Git update failed")
        return False
    for _ in range(3):
        if pip_manager.update():
            break
    else:
        logger.warning("Pip update failed")
        return False
    
    return True


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

    if run_update():
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
            have_update = git_manager.check_update()
        if not have_update:
            th._task.delay = get_next_time(schedule_time)
            yield
            continue

        update()
        th._task.delay = get_next_time(schedule_time)
        yield



if __name__ == '__main__':
    pass
    if git_manager.check_update():
        git_manager.update()
    pip_manager.update()
