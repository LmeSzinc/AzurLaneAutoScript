from dataclasses import dataclass
from typing import ClassVar

from module.ocr.keyword import Keyword


@dataclass(repr=False)
class ItemTab(Keyword):
    instances: ClassVar = {}
