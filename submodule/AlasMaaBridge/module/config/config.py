import os
from datetime import datetime

from module.config.config import AzurLaneConfig, name_to_function
from module.config.utils import filepath_config

from submodule.AlasMaaBridge.module.config.config_generated import GeneratedConfig
from submodule.AlasMaaBridge.module.config.config_updater import ConfigUpdater


class ArknightsConfig(AzurLaneConfig, ConfigUpdater, GeneratedConfig):
    SCHEDULER_PRIORITY = """
            MaaStartup
            > MaaRecruit > MaaInfrast
            > MaaVisit > MaaMall
            > MaaAnnihilation > MaaMaterial
            > MaaFight > MaaAward
            > MaaRoguelike
            """

    def __init__(self, config_name, task=None):
        super().__init__(config_name, task)
        if task is None:
            task = name_to_function("Maa")
            self.bind(task)
            self.task = task
            self.save()

    def bind(self, func, func_set=None):
        if func_set is None:
            func_set = {'Maa'}
        super().bind(func, func_set)

    def save(self, mod_name='maa'):
        super().save(mod_name)

    def get_mtime(self):
        timestamp = os.stat(filepath_config(self.config_name, mod_name='maa')).st_mtime
        mtime = datetime.fromtimestamp(timestamp).replace(microsecond=0)
        return mtime


def load_config(config_name, task):
    return ArknightsConfig(config_name, task)
