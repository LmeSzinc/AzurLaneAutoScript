import multiprocessing
import threading
from multiprocessing.managers import SyncManager

from module.config.config_updater import ConfigUpdater
from module.webui.config import DeployConfig


class State:
    """
    Shared settings
    """

    _init = False
    _clearup = False

    deploy_config = DeployConfig()
    config_updater = ConfigUpdater()
    restart_event: threading.Event = None
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
