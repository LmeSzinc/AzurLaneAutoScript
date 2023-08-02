import re
from dataclasses import dataclass
from typing import ClassVar

from module.ocr.keyword import Keyword


@dataclass(repr=False)
class BattlePassTab(Keyword):
    instances: ClassVar = {}


@dataclass(repr=False)
class BattlePassMissionTab(Keyword):
    instances: ClassVar = {}


@dataclass(repr=False)
class BattlePassQuest(Keyword):
    instances: ClassVar = {}

    @classmethod
    def _compare(cls, name, keyword):
        def remove_digit(text):
            return re.sub(r"\d", "", text)

        return remove_digit(name) == remove_digit(keyword)


@dataclass(repr=False)
class BattlePassQuestState(Keyword):
    instances: ClassVar = {}
