import multiprocessing
import threading
from multiprocessing.managers import SyncManager
from typing import TYPE_CHECKING

from module.base.decorator import cached_class_property

if TYPE_CHECKING:
    from module.config.config_updater import ConfigUpdater
    from module.webui.config import DeployConfig


class State:
    """
    Shared settings
    """

    _init = False
    _clearup = False

    restart_event: threading.Event = None
    manager: SyncManager = None
    theme: str = "dark"

    @classmethod
    def init(cls):
        cls.manager = multiprocessing.Manager()
        cls._init = True

    @classmethod
    def clearup(cls):
        cls.manager.shutdown()
        cls._clearup = True

    @cached_class_property
    def deploy_config(self) -> "DeployConfig":
        """
        Returns:
            DeployConfig：
        """
        from module.webui.config import DeployConfig

        return DeployConfig()

    @cached_class_property
    def config_updater(self) -> "ConfigUpdater":
        """
        Returns:
            ConfigUpdater：
        """
        from module.config.config_updater import ConfigUpdater

        return ConfigUpdater()
