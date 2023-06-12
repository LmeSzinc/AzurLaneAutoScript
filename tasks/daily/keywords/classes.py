from dataclasses import dataclass
from typing import ClassVar

from module.ocr.keyword import Keyword


@dataclass
class DailyQuest(Keyword):
    instances: ClassVar = {}
