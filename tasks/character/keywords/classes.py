from dataclasses import dataclass
from typing import ClassVar

from module.base.decorator import cached_property
from module.ocr.keyword import Keyword


@dataclass(repr=False)
class CharacterList(Keyword):
    instances: ClassVar = {}

    @cached_property
    def is_trailblazer(self) -> bool:
        return 'Trailblazer' in self.name

    def __hash__(self) -> int:
        return super().__hash__()
