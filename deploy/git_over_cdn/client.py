import io
import json
import os
import re
import shutil
import subprocess
import zipfile
from typing import Callable, Generic, TypeVar

import requests
from requests.adapters import HTTPAdapter

T = TypeVar("T")

TEMPLATE_FILE = './config/template.yaml'


class cached_property(Generic[T]):
    """
    cached-property from https://github.com/pydanny/cached-property
    Add typing support

    A property that is only computed once per instance and then replaces itself
    with an ordinary attribute. Deleting the attribute resets the property.
    Source: https://github.com/bottlepy/bottle/commit/fa7733e075da0d790d809aa3d2f53071897e6f76
    """

    def __init__(self, func: Callable[..., T]):
        self.func = func

    def __get__(self, obj, cls) -> T:
        if obj is None:
            return self

        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


class PrintLogger:
    info = print
    warning = print
    error = print

    @staticmethod
    def attr(name, text):
        print(f'[{name}] {text}')


class GitOverCdnClient:
    logger = PrintLogger()

    def __init__(self, url, folder, source='origin', branch='master', git='git'):
        """
        Args:
            url: http://127.0.0.1:22251/pack/LmeSzinc_AzurLaneAutoScript_master/
            folder: D:/AzurLaneAutoScript
        """
        self.url = url.strip('/')
        self.folder = folder.replace('\\', '/')
        self.source = source
        self.branch = branch
        self.git = git

    def filepath(self, path):
        path = os.path.join(self.folder, '.git', path)
        return os.path.abspath(path).replace('\\', '/')

    def urlpath(self, path):
        return f'{self.url}{path}'

    @cached_property
    def current_commit(self) -> str:
        for file in [
            f'./refs/remotes/{self.source}/{self.branch}',
            f'./refs/heads/{self.branch}',
            'ORIG_HEAD',
        ]:
            file = self.filepath(file)
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    commit = f.read()
                res = re.search(r'([0-9a-f]{40})', commit)
                if res:
                    commit = res.group(1)
                    self.logger.attr('CurrentCommit', commit)
                    return commit
            except FileNotFoundError as e:
                self.logger.error(f'Failed to get local commit: {e}')
            except Exception as e:
                self.logger.error(f'Failed to get local commit: {e}')
        return ''

    @property
    def session(self):
        session = requests.Session()
        session.trust_env = False
        session.mount('http://', HTTPAdapter(max_retries=3))
        session.mount('https://', HTTPAdapter(max_retries=3))
        return session

    @cached_property
    def latest_commit(self) -> str:
        try:
            url = self.urlpath('/latest.json')
            self.logger.info(f'Fetch url: {url}')
            resp = self.session.get(url, timeout=3)
        except Exception as e:
            self.logger.error(f'Failed to get remote commit: {e}')
            return ''

        if resp.status_code == 200:
            try:
                info = json.loads(resp.text)
                commit = info['commit']
                self.logger.attr('LatestCommit', commit)
                return commit
            except json.JSONDecodeError:
                self.logger.error(f'Failed to get remote commit, response is not a json: {resp.text}')
                return ''
            except KeyError:
                self.logger.error(f'Failed to get remote commit, key "commit" is not found: {resp.text}')
                return ''
        else:
            self.logger.error(f'Failed to get remote commit, status={resp.status_code}, text={resp.text}')
            return ''

    def download_pack(self):
        try:
            url = self.urlpath(f'/{self.latest_commit}/{self.current_commit}.zip')
            self.logger.info(f'Fetch url: {url}')
            resp = self.session.get(url, timeout=20)
        except Exception as e:
            self.logger.error(f'Failed to download pack: {e}')
            return False

        if resp.status_code == 200:
            try:
                zipped = zipfile.ZipFile(io.BytesIO(resp.content))
                for file in [f'pack-{self.latest_commit}.pack', f'pack-{self.latest_commit}.idx']:
                    self.logger.info(f'Unzip {file}')
                    member = zipped.getinfo(file)
                    tmp = self.filepath(f'./objects/pack/{file}.tmp')
                    out = self.filepath(f'./objects/pack/{file}')
                    with zipped.open(member) as source, open(tmp, "wb") as target:
                        shutil.copyfileobj(source, target)
                    os.replace(tmp, out)
                return True
            except zipfile.BadZipFile as e:
                # File is not a zip file
                self.logger.error(e)
                return False
            except KeyError as e:
                # There is no item named 'xxx.idx' in the archive
                self.logger.error(e)
                return False
            except Exception as e:
                self.logger.error(e)
                return False
        elif resp.status_code == 404:
            self.logger.error(f'Failed to download pack, status={resp.status_code}, no such pack files provided')
            return False
        else:
            self.logger.error(f'Failed to download pack, status={resp.status_code}, text={resp.text}')
            return False

    def update_refs(self):
        file = self.filepath(f'./refs/remotes/{self.source}/{self.branch}')
        text = f'{self.latest_commit}\n'
        self.logger.info(f'Update refs: {file}')
        os.makedirs(os.path.dirname(file), exist_ok=True)
        try:
            with open(file, 'w', encoding='utf-8', newline='') as f:
                f.write(text)
            return True
        except FileNotFoundError as e:
            self.logger.error(f'Failed to get local commit: {e}')
        except Exception as e:
            self.logger.error(f'Failed to get local commit: {e}')

        return False

    def git_command(self, *args, timeout=300):
        """
        Execute ADB commands in a subprocess,
        usually to be used when pulling or pushing large files.

        Args:
            timeout (int):

        Returns:
            str:
        """
        os.chdir(self.folder)
        cmd = list(map(str, args))
        cmd = [self.git] + cmd
        self.logger.info(f'Execute: {cmd}')

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=False)
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            self.logger.warning(f'TimeoutExpired when calling {cmd}, stdout={stdout}, stderr={stderr}')
        return stdout.decode()

    def git_reset(self, keep_changes=False):
        """
        git reset --hard <commit>
        """
        # Remove git lock
        for lock_file in [
            './.git/index.lock',
            './.git/HEAD.lock',
            './.git/refs/heads/master.lock',
        ]:
            if os.path.exists(lock_file):
                self.logger.info(f'Lock file {lock_file} exists, removing')
                os.remove(lock_file)
        if keep_changes:
            self.git_command('stash')
            self.git_command('reset', '--hard', f'{self.source}/{self.branch}')
            self.git_command('stash', 'pop')
        else:
            self.git_command('reset', '--hard', f'{self.source}/{self.branch}')

    def get_status(self):
        """
        Returns:
            str: 'uptodate' if repo is up-to-date
                'behind' if repos is not up-to-date
                'failed' if failed
        """
        _ = self.current_commit
        _ = self.latest_commit
        if not self.current_commit:
            self.logger.error('Failed to get current commit')
            return 'failed'
        if not self.latest_commit:
            self.logger.error('Failed to get latest commit')
            return 'failed'
        if self.current_commit == self.latest_commit:
            self.logger.info('Already up to date')
            return 'uptodate'
        self.logger.info('Current repo is behind remote')
        return 'behind'

    def update(self, keep_changes=False):
        """
        Args:
            keep_changes:

        Returns:
            bool: If repo is up-to-date
        """
        _ = self.current_commit
        _ = self.latest_commit
        if not self.current_commit:
            self.logger.error('Failed to get current commit')
            return False
        if not self.latest_commit:
            self.logger.error('Failed to get latest commit')
            return False
        if self.current_commit == self.latest_commit:
            self.logger.info('Already up to date')
            self.git_reset(keep_changes=keep_changes)
            return True

        if not self.download_pack():
            return False
        if not self.update_refs():
            return False
        self.git_reset(keep_changes=keep_changes)
        self.logger.info('Update success')
        return True
