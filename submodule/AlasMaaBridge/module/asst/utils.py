from typing import Union, Dict, List, Any, Type
from enum import Enum, IntEnum, unique, auto

JSON = Union[Dict[str, Any], List[Any], int, str, float, bool, Type[None]]


class InstanceOptionType(IntEnum):
    # 触控模式设置， "minitouch" | "maatouch" | "adb"
    touch_type = 2
    # 自动战斗、肉鸽、保全 是否使用 暂停下干员， "0" | "1"
    deployment_with_pause = 3
    # 是否使用 AdbLite， "0" | "1"
    adblite_enabled = 4
    kill_on_adb_exit = 5


class StaticOptionType(IntEnum):
    invalid = 0
    cpu_ocr = 1
    gpu_ocr = 2


@unique
class Message(Enum):
    """
    回调消息

    请参考 docs/回调消息.md
    """
    InternalError = 0

    InitFailed = auto()

    ConnectionInfo = auto()

    AllTasksCompleted = auto()

    AsyncCallInfo = auto()

    Destroyed = auto()

    TaskChainError = 10000

    TaskChainStart = auto()

    TaskChainCompleted = auto()

    TaskChainExtraInfo = auto()

    TaskChainStopped = auto()

    SubTaskError = 20000

    SubTaskStart = auto()

    SubTaskCompleted = auto()

    SubTaskExtraInfo = auto()

    SubTaskStopped = auto()


@unique
class Version(Enum):
    """
    目标版本
    """
    Nightly = auto()

    Beta = auto()

    Stable = auto()
