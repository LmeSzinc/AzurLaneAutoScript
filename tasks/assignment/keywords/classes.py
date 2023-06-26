from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar

from module.ocr.keyword import Keyword


@dataclass(repr=False)
class AssignmentGroup(Keyword):
    instances: ClassVar = {}
    entries: tuple[AssignmentEntry] = ()


@dataclass(repr=False)
class AssignmentEntry(Keyword):
    instances: ClassVar = {}
    group: AssignmentGroup = None
    def __hash__(self) -> int:
        return super().__hash__()

