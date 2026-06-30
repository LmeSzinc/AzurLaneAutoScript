import os
from datetime import datetime

from module.config.config import AzurLaneConfig, name_to_function
from module.config.utils import filepath_config

from submodule.AlasFpyBridge.module.config.config_generated import GeneratedConfig
from submodule.AlasFpyBridge.module.config.config_updater import ConfigUpdater


class FgoConfig(AzurLaneConfig, ConfigUpdater, GeneratedConfig):
    SCHEDULER_PRIORITY = """
        FpyMain
      > FpyDailyFpSummon
      > FpyHeartbeat
    """

    # @override
    def __init__(self, config_name, task=None):
        super().__init__(config_name, task)
        if task is None:
            task = name_to_function("Fpy")
            self.bind(task)
            self.task = task
            self.save()

    # @override
    def bind(self, func, func_list=None):
        if func_list is None:
            func_list = ["Fpy"]
        super().bind(func, func_list)

    # @override
    def save(self, mod_name="fpy"):
        super().save(mod_name)

    # @override
    def get_mtime(self):
        timestamp = os.stat(filepath_config(self.config_name, mod_name="fpy")).st_mtime
        mtime = datetime.fromtimestamp(timestamp).replace(microsecond=0)
        return mtime


def load_config(config_name, task):
    return FgoConfig(config_name, task)
