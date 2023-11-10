import tasks.character.keywords.character_list as KEYWORD_CHARACTER_LIST
from tasks.character.keywords.character_list import *
from tasks.character.keywords.classes import CharacterList

DICT_SORTED_RANGES = {
    # Mage, hit instantly, no trajectories
    'Mage': [
        DanHengImbibitorLunae,
        Welt,
        FuXuan,
    ],
    # Mage, but character moved after attack
    'MageSecondary': [
        Yanqing,
    ],
    # Archer
    'Archer': [
        Yukong,
        TopazandNumby,
        March7th,
        Bronya,
        Asta,
        Pela,
        Qingque,
    ],
    # Archer, but her parabolic trajectory has 0% accuracy on moving targets
    'ArcherSecondary': [
        Natasha,
    ],
    # Melee
    # rest of the characters are classified as melee and will not be switched to
}
