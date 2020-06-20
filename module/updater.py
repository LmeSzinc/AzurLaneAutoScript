import json
import datetime
from urllib import error, request
import requests
from module.logger import logger
from module.config.config import AzurLaneConfig

class Update(object):

    def __init__(self, config):
        """
        Args:
            config(AzurLaneConfig):
        """
        self.config = config

    def check_update(self):
        main_commits = 'https://api.github.com/repos/LmeSzinc/AzurLaneAutoScript/commits/master'
        fork_commits = 'https://api.github.com/repos/whoamikyo/AzurLaneAutoScript/commits/master'

        # LmeSzinc commits
        l = requests.get(main_commits)
        main_commit_info = json.loads(l.content)

        # Whoamikyo fork commits
        w = requests.get(fork_commits)
        fork_commit_info = json.loads(w.content)

        _file = open('version.txt', 'r')
        local_version = _file.read()
        local_lmeszinc = local_version.splitlines()[1]
        local_whoamikyo = local_version.splitlines()[2]

        # date_time_local = datetime.datetime.strptime(local_version, '%Y%m%d.%S')
        date_time_lmeszinc = datetime.datetime.strptime(local_lmeszinc, '%Y%m%d.%S')
        date_time_whoamikyo = datetime.datetime.strptime(local_whoamikyo, '%Y%m%d.%S')

        if self.config.UPDATE_CHECK:

            try:
                with request.urlopen("https://raw.githubusercontent.com/LmeSzinc/AzurLaneAutoScript/master/version.txt") as m:
                    _m = m.read().decode('utf-8')
                    main_version = _m.splitlines()[1]
                    main_version_date = datetime.datetime.strptime(main_version, '%Y%m%d.%S')
                    _file.close()
                    if main_version_date > date_time_lmeszinc:
                        logger.warning('A new update is available on LmeSzinc repository, please run Easy_Install-V2.bat or check github')
                    else:
                        logger.info('ALAS is up to date with LmeSzinc repository')
            except error.HTTPError as e:
                logger.error("Couldn't check for updates, {}.".format(e))

            else:

                try:
                    with request.urlopen("https://raw.githubusercontent.com/whoamikyo/AzurLaneAutoScript/master/version.txt") as f:
                        _f = f.read().decode('utf-8')
                        fork_version = _f.splitlines()[2]
                        fork_version_date = datetime.datetime.strptime(fork_version, '%Y%m%d.%S')
                        _file.close()
                        if fork_version_date > date_time_whoamikyo:
                            logger.warning('A new update is available on whoamikyo repository, please run Easy_Install-V2.bat or check github')
                        else:
                            logger.info('ALAS is up to date with whoamikyo repository')
                            logger.info('Latest commit from\n%s - %s' % (
                            main_commit_info['commit']['author']['name'], main_commit_info['commit']['message']))
                            logger.info('Latest commit from\n%s - %s' % (
                            fork_commit_info['commit']['author']['name'], fork_commit_info['commit']['message']))
                except error.HTTPError as e:
                    logger.error("Couldn't check for updates, {}.".format(e))

                # if local_version != fork_version:
                #     logger.warning("Current Version: " + local_version)
                #     logger.warning("Current LmeSzinc version: " + main_version)
                #     logger.warning("Current whoamikyo version: " + fork_version)
                #     logger.warning('A new update is available, please run Easy_Install-V2.bat or check github')
                #
                # else:
                #     logger.info('ALAS is up to date')
                #     logger.warning("Current Version: " + local_version)
                #     logger.info('Latest commit from\n%s - %s' % (main_commit_info['commit']['author']['name'], main_commit_info['commit']['message']))
                #     logger.info('Latest commit from\n%s - %s' % (fork_commit_info['commit']['author']['name'], fork_commit_info['commit']['message']))

                    return True








