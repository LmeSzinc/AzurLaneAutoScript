import os
from datetime import datetime

from module.config.utils import filepath_config, DEFAULT_TIME
from module.logger import logger


class ConfigWatcher:
    config_name = 'alas'
    start_mtime = DEFAULT_TIME

    def start_watching(self) -> None:
        self.start_mtime = self.get_mtime()

    def get_mtime(self) -> datetime:
        """
        Last modify time of the file
        """
        timestamp = os.stat(filepath_config(self.config_name)).st_mtime
        mtime = datetime.fromtimestamp(timestamp).replace(microsecond=0)
        return mtime

    def should_reload(self) -> bool:
        """
        Returns:
            bool: Whether the file has been modified and configs should reload
        """
        mtime = self.get_mtime()
        if mtime > self.start_mtime:
            logger.info(f'Config "{self.config_name}" changed at {mtime}')
            return True
        else:
            return False
