from module.config.config import AzurLaneConfig

"""
Return default values, since submodules shouldn't have nested submodules
"""


def start_ocr_server_process(*args, **kwargs):
    pass


def stop_ocr_server_process(*args, **kwargs):
    pass


def load_config(config_name):
    return AzurLaneConfig(config_name, '')


def get_config_mod(config_name):
    """
    Args:
        config_name (str):
    """
    return 'alas'


def list_mod():
    return []


def mod_instance():
    return []


def init_discord_rpc():
    pass


def close_discord_rpc():
    pass
