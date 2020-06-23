import json
import re
import subprocess
from datetime import datetime

import requests
from lxml import etree

from module.config.config import AzurLaneConfig
from module.logger import logger, pyw_name
from module.base.decorator import Config


class Update:
    def __init__(self, config):
        """
        Args:
            config (AzurLaneConfig):
        """
        self.config = config

    @staticmethod
    def github_api(author, token):
        return f'https://api.github.com/repos/{author}/AzurLaneAutoScript/commits?access_token={token}'

    @staticmethod
    def github_commit(author):
        return f'https://github.com/{author}/AzurLaneAutoScript/commits/master'

    @Config.when(UPDATE_METHOD='api')
    def get_github_commit(self, author, token=None, proxy=None):
        """
        Args:
            author (str):
            token (str): To generate your token visit https://github.com/settings/tokens
            proxy (str): Local http or socks proxy, example: http://127.0.0.1:10809, socks://127.0.0.1:10808
                Need to install requests[socks], if using a socks proxy.

        Returns:
            datetime.datetime, str
        """
        if proxy:
            proxy = {'http': proxy, 'https': proxy}
        resp = requests.get(self.github_api(author, token), proxies=proxy)
        if resp.status_code != 200:
            logger.warning(f'{resp.status_code} {self.github_commit(author)}')
        resp.encoding = 'utf-8'
        data = json.loads(resp.content)

        pattern = re.compile('^[Mm]erge')
        for commit in data:
            if re.search(pattern, commit['commit']['message']):
                continue

            date = datetime.strptime(commit['commit']['author']['date'], '%Y-%m-%dT%H:%M:%SZ')
            return date, author

        logger.warning(f'No commit found. author={author}')

    @Config.when(UPDATE_METHOD='web')
    def get_github_commit(self, author, token=None, proxy=None):
        """
        Args:
            author (str):
            token (str): To generate your token visit https://github.com/settings/tokens
            proxy (str): Local http or socks proxy, example: http://127.0.0.1:10809, socks://127.0.0.1:10808
                Need to install requests[socks], if using a socks proxy.

        Returns:
            datetime.datetime, str
        """
        if proxy:
            proxy = {'http': proxy, 'https': proxy}
        resp = requests.get(self.github_commit(author), proxies=proxy)
        if resp.status_code != 200:
            logger.warning(f'{resp.status_code} {self.github_commit(author)}')
        resp.encoding = 'utf-8'

        tree = etree.HTML(resp.content)
        message_list = tree.xpath('//a[contains(@class, "message")]/text()')
        date_list = tree.xpath('//relative-time/@datetime')
        pattern = re.compile('^[Mm]erge')
        for message, date in zip(message_list, date_list):
            if re.search(pattern, message):
                continue

            date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
            return date, author
        logger.warning(f'No commit found. author={author}')

    @staticmethod
    def get_local_commit():
        """
        Returns:
            datetime.datetime, str
        """
        cmd = ['git', 'log', '--no-merges', '-1']
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        result, error = process.communicate(timeout=4)
        result = result.decode("utf-8")
        if error:
            logger.warning('Failed to get local git commit')
            return None
        date = datetime.strptime(result.split('\n')[2][8:], '%a %b %d %H:%M:%S %Y %z')
        date -= date.utcoffset()
        date = date.replace(tzinfo=None)

        return date, '<local version>'

    def get_latest_commit(self):
        """
        Returns:
            datetime.datetime, str

        Logs:
                  Time                 Author
            old:  2020-06-20_09:12:19  <local>
                  2020-06-20_10:12:19  whoamikyo
            new:  2020-06-20_11:12:19  LmeSzinc
        """
        if pyw_name != 'alas' or not self.config.UPDATE_CHECK:
            # Disable when using multiple Alas.
            return False

        logger.hr('Update Check')
        commits = [
            self.get_github_commit('whoamikyo', token=self.config.GITHUB_TOKEN, proxy=self.config.UPDATE_PROXY),
            self.get_github_commit('LmeSzinc', token=self.config.GITHUB_TOKEN, proxy=self.config.UPDATE_PROXY),
        ]
        local = self.get_local_commit()
        if local is not None:
            commits.append(local)
        commits.sort(key=lambda x: x[0])

        text = [f'{commit[0]}  {commit[1]}' for commit in commits]
        text.insert(0, 'Time(UTC)            Author')
        for index, line in enumerate(text):
            if index == 1:
                logger.info(f'old:  {line}')
            elif index == len(text) - 1:
                logger.info(f'new:  {line}')
            else:
                logger.info(f'      {line}')

        if commits[-1][1] != '<local version>' and local is not None:
            logger.warning('A new update is available')
