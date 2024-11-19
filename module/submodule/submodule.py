import importlib

from module.logger import logger
from module.submodule.utils import *


def load_mod(name):
    dir_name = get_mod_dir(name)
    if dir_name is None:
        logger.critical("No function matched")
        return

    return importlib.import_module('.' + name, 'submodule.' + dir_name)


def load_config(config_name):
    from module.config.config import AzurLaneConfig

    mod_name = get_config_mod(config_name)
    if mod_name == 'alas':
        return AzurLaneConfig(config_name, '')
    else:
        config_lib = importlib.import_module(
            '.config',
            'submodule.' + get_mod_dir(mod_name) + '.module.config')
        return config_lib.load_config(config_name, '')

