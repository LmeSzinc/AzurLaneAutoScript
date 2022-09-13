import os
from datetime import datetime

from module.config.config import GeneralConfig, Function, name_to_function
from module.config.utils import path_to_arg, filepath_config
from module.logger import logger

from submodule.AlasMaaBridge.module.config.config_generated import GeneratedConfig
from submodule.AlasMaaBridge.module.config.config_manual import ManualConfig
from submodule.AlasMaaBridge.module.config.config_updater import ConfigUpdater


class ArknightsConfig(GeneralConfig, ConfigUpdater, ManualConfig, GeneratedConfig):
    def __init__(self, config_name, task=None):
        super().__init__(config_name, task)
        if task is None:
            task = name_to_function("Maa")
            self.bind(task)
            self.task = task
            self.save()

    def bind(self, func):
        """
        Args:
            func (str, Function): Function to run
        """
        if isinstance(func, Function):
            func = func.command
        func_set = {func, "Maa"}

        logger.info(f"Bind task {func_set}")

        # Bind arguments
        visited = set()
        self.bound.clear()
        for func in func_set:
            func_data = self.data.get(func, {})
            for group, group_data in func_data.items():
                for arg, value in group_data.items():
                    path = f"{group}.{arg}"
                    if path in visited:
                        continue
                    arg = path_to_arg(path)
                    super().__setattr__(arg, value)
                    self.bound[arg] = f"{func}.{path}"
                    visited.add(path)

        # Override arguments
        for arg, value in self.overridden.items():
            super().__setattr__(arg, value)

    def save(self, mod_name='maa'):
        super().save(mod_name)

    def get_mtime(self) -> datetime:
        timestamp = os.stat(filepath_config(self.config_name, mod_name='maa')).st_mtime
        mtime = datetime.fromtimestamp(timestamp).replace(microsecond=0)
        return mtime


def load_config(config_name, task):
    return ArknightsConfig(config_name, task)
