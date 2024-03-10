from dataclasses import dataclass
from typing import ClassVar

from module.base.decorator import cached_property
from module.ocr.keyword import Keyword


@dataclass(repr=False)
class CharacterList(Keyword):
    instances: ClassVar = {}

    def __hash__(self) -> int:
        return super().__hash__()

    @cached_property
    def is_trailblazer(self) -> bool:
        return 'Trailblazer' in self.name

    @cached_property
    def height(self) -> str:
        """
        Returns:
            str: Character height, from list ['Kid', 'Girl', 'Boy', 'Maid', 'Miss', 'Lady', 'Lad', 'Male']
                or 'Unknown' if no data
        """
        from tasks.character.keywords.height import CHARACTER_HEIGHT
        return CHARACTER_HEIGHT.get(self.name, 'Unknown')


@dataclass(repr=False)
class CombatType(Keyword):
    instances: ClassVar = {}

    def __hash__(self) -> int:
        return super().__hash__()
