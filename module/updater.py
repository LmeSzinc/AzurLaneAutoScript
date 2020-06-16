from urllib import error, request
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
        version = ''
        latest_version = ''
        _file = open('version.txt', 'r')

        if self.config.UPDATE:
            version = _file.readline()

            try:
                with request.urlopen("https://raw.githubusercontent.com/whoamikyo/AzurLaneAutoScript/master/version.txt") as f:
                    _f = f.read().decode('utf-8')
                    latest_version = _f.splitlines()[1]
            except error.HTTPError as e:
                logger.info("Couldn't check for updates, {}.".format(e))

        else:
            version = _file.readlines()[1]

            try:
                with request.urlopen("https://raw.githubusercontent.com/whoamikyo/AzurLaneAutoScript/master/version.txt") as f:
                    _f = f.read().decode('utf-8')
                    latest_version = _f.splitlines()[1]
            except error.HTTPError as e:
                logger.info("Couldn't check for updates, {}.".format(e))

        _file.close()

        if version != latest_version:
            logger.info("Current version: " + version)
            logger.info("Latest version: " + latest_version)

            return True