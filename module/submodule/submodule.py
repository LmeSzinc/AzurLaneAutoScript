import os
import importlib

from module.config.config import AzurLaneConfig
from module.logger import logger
from module.submodule.utils import *


def load_mod(name):
    for mod_name, dir_name in list_mod():
        if name == mod_name:
            mod = importlib.import_module('.' + name, 'submodule.' + dir_name)
            return mod

    logger.critical("No function matched")


def load_config(config_name):
    mod_name = get_config_mod(config_name)
    if mod_name == 'alas':
        return AzurLaneConfig(config_name, '')
    else:
        config_lib = importlib.import_module(
            '.config',
            'submodule.' + get_dir_name(mod_name) + '.module.config')
        config = config_lib.load_config(config_name, '')
        return config_lib.load_config(config_name, '')

