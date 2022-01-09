import datetime
import os
import subprocess
import threading
import time
from typing import Generator

import requests
from deploy.installer import DeployConfig, cached_property
from deploy.utils import DEPLOY_CONFIG
from module.logger import logger


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
            platform = 'gitee'
            list_commit_api = f"https://gitee.com/api/v5/repos/{owner}/{repo}/branches/{self.branch}"
            get_commit_api = f"https://gitee.com/api/v5/repos/{owner}/{repo}/commits/"
            headers = {}
        else:
            platform = 'github'
            list_commit_api = f"https://api.github.com/repos/{owner}/{repo}/commits"
            get_commit_api = list_commit_api + '/'
            headers = {
                'Accept': 'application/vnd.github.v3.sha'
            }

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
            list_commit = requests.get(list_commit_api, headers=headers)
            get_commit = requests.get(
                get_commit_api + local_sha, headers=headers)
        except Exception as e:
            logger.exception(e)
            logger.warning("Check update failed")
            return False

        if get_commit.status_code != 200:
            # for develops
            logger.info(
                f"Cannot find local commit {local_sha[:8]} in upstream, skip update")
            return False

        if list_commit.status_code != 200:
            logger.warning(
                f"Check update failed, code {list_commit.status_code}")
            return False
        try:
            if platform == 'github':
                sha = list_commit.json()[0]['sha']
            else:
                sha = list_commit.json()['commit']['sha']
        except Exception as e:
            logger.exception(e)
            logger.warning("Check update failed when parsing return json")
            return False

        if sha == local_sha:
            logger.info("No update")
            return False

        logger.info(f"Update {sha[:8]} avaliable")
        return True

    def update(self):
        source = 'origin'
        self.execute(f'"{self.git}" init')
        if self.to_bool(self.proxy):
            self.execute(
                f'"{self.git}" config --local http.proxy {self.proxy}')
            self.execute(
                f'"{self.git}" config --local https.proxy {self.proxy}')
        else:
            self.execute(f'"{self.git}" config --local --unset http.proxy')
            self.execute(f'"{self.git}" config --local --unset https.proxy')

        if not self.execute(f'"{self.git}" remote set-url {source} {self.repo}'):
            self.execute(f'"{self.git}" remote add {source} {self.repo}')

        # self.execute(f'"{self.git}" fetch {source} {self.branch}')

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


class PipManager(Config):
    pass


have_update = False
git_manager = GitManager()
delay = int(git_manager.config['CheckUpdateInterval'])*60
schedule_time = datetime.time.fromisoformat(
    git_manager.config['AutoRestartTime'])
event: threading.Event = None


def update_state() -> Generator:
    global have_update
    yield
    while True:
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
        break
        if pip_manager.update():
            break
    else:
        logger.warning("Pip update failed")
        return False
    
    return True

if __name__ == '__main__':
    pass
    # if git_manager.check_update():
    #     git_manager.update()
