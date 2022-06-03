import multiprocessing
import threading
from multiprocessing.managers import SyncManager

from module.config.config_updater import ConfigUpdater
from module.webui.config import WebuiConfig


class State:
    """
    Shared settings
    """

    _init = False
    _clearup = False

    webui_config = WebuiConfig()
    config_updater = ConfigUpdater()
    researt_event: threading.Event = None
    manager: SyncManager = None
    electron: bool = False
    theme: str = "default"

    @classmethod
    def init(cls):
        cls.manager = multiprocessing.Manager()
        cls._init = True

    @classmethod
    def clearup(cls):
        cls.manager.shutdown()
        cls._clearup = True
