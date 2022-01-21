import multiprocessing
from module.config.config_updater import ConfigUpdater
from module.webui.config import WebuiConfig
from multiprocessing.managers import SyncManager


class Setting:
    """
    Shared settings
    """
    _init = False
    _clearup = False

    webui_config = WebuiConfig()
    config_updater = ConfigUpdater()
    manager: SyncManager = None
    reload: bool = False
    electron: bool = False
    theme: str = 'default'

    @classmethod
    def init(cls):
        cls.manager = multiprocessing.Manager()
        cls._init = True

    @classmethod
    def clearup(cls):
        cls.manager.shutdown()
        cls._clearup = True
