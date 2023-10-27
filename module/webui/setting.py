import multiprocessing
import threading
from multiprocessing.managers import SyncManager
from typing import TYPE_CHECKING, Callable, Generic, TypeVar

if TYPE_CHECKING:
    from module.config.config_updater import ConfigUpdater
    from module.webui.config import DeployConfig

T = TypeVar("T")


class cached_class_property(Generic[T]):
    """
    Code from https://github.com/dssg/dickens
    Add typing support

    Descriptor decorator implementing a class-level, read-only
    property, which caches its results on the class(es) on which it
    operates.
    Inheritance is supported, insofar as the descriptor is never hidden
    by its cache; rather, it stores values under its access name with
    added underscores. For example, when wrapping getters named
    "choices", "choices_" or "_choices", each class's result is stored
    on the class at "_choices_"; decoration of a getter named
    "_choices_" would raise an exception.
    """

    class AliasConflict(ValueError):
        pass

    def __init__(self, func: Callable[..., T]):
        self.__func__ = func
        self.__cache_name__ = '_{}_'.format(func.__name__.strip('_'))
        if self.__cache_name__ == func.__name__:
            raise self.AliasConflict(self.__cache_name__)

    def __get__(self, instance, cls=None) -> T:
        if cls is None:
            cls = type(instance)

        try:
            return vars(cls)[self.__cache_name__]
        except KeyError:
            result = self.__func__(cls)
            setattr(cls, self.__cache_name__, result)
            return result


class State:
    """
    Shared settings
    """

    _init = False
    _clearup = False

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
