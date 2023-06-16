from dataclasses import dataclass
from typing import ClassVar

from module.ocr.keyword import Keyword


@dataclass(repr=False)
class DailyQuest(Keyword):
    instances: ClassVar = {}


@dataclass(repr=False)
class DailyQuestState(Keyword):
    instances: ClassVar = {}
