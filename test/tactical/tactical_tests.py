import sys
import unittest

from module.base.utils import load_image
from module.config.config import AzurLaneConfig
from module.device.debug_device import DebugDevice
from module.logger import logger
from module.tactical.assets import TACTICAL_SKILL_LEVEL_1
from module.tactical.tactical_class import RewardTacticalClass
from module.ui.assets import TACTICAL_CHECK

sys.path.append('././')

default_config = AzurLaneConfig('alas', 'Tactical')
logger.setLevel('WARNING')


def test_body(image_location=None):
    return RewardTacticalClass(
        config=default_config,
        device=DebugDevice(image_location=image_location)
    )


class TestTactical(unittest.TestCase):

    def test_receive_should_end(self):
        image = 'D:/project/AlasTest/tactical/MAIN.png'
        assert test_body(image).appear_for_seconds(TACTICAL_CHECK, 1), \
            'Error in appear_for_seconds().'

    def test_receive_should_not_end(self):
        images = [
            'D:/project/AlasTest/tactical/MAIN.png',
            'D:/project/AlasTest/tactical/DOCK.png',
            'D:/project/AlasTest/tactical/MAIN.png',
            'D:/project/AlasTest/tactical/MAIN.png',
            'D:/project/AlasTest/tactical/DOCK.png'
        ]
        assert not test_body(images).appear_for_seconds(TACTICAL_CHECK, 1), \
            'Error in appear_for_seconds().'

    def test_find_empty_position(self):
        image = 'D:/project/AlasTest/tactical/MAIN_TWO_POSITION.png'
        assert test_body(image).find_empty_position(), 'Should find a position.'

    def test_find_empty_position_2(self):
        image = 'D:/project/AlasTest/tactical/MAIN_ONE_POSITION.png'
        assert test_body(image).find_empty_position(), 'Should find a position.'

    def test_not_find_empty_position(self):
        image = 'D:/project/AlasTest/tactical/MAIN_NO_POSITION.png'
        assert not test_body(image).find_empty_position(), 'Should not find a position.'

    def test_select_suitable_ship_1(self):
        image = 'D:/project/AlasTest/tactical/DOCK_NORMAL.png'
        assert test_body(image).select_suitable_ship(), 'Should find first ship'

    def test_select_suitable_ship_2(self):
        image = 'D:/project/AlasTest/tactical/DOCK_ONLY_META.png'
        assert test_body(image).select_suitable_ship(), 'Should find meta ship'

    def test_select_suitable_ship_3(self):
        image = 'D:/project/AlasTest/tactical/DOCK_ONLY_META.png'
        assert not test_body(image).select_suitable_ship(skip_meta=1), 'Should not find a ship'

    def test_select_suitable_ship_4(self):
        image = 'D:/project/AlasTest/tactical/DOCK_EMPTY.png'
        assert not test_body(image).select_suitable_ship(), 'Empty Dock should not find a ship'

    def test_check_meta_1(self):
        image = 'D:/project/AlasTest/tactical/SKILL_META.png'
        assert test_body(image).check_meta(), 'It is meta skill list'

    def test_check_meta_2(self):
        image = 'D:/project/AlasTest/tactical/SKILL_NORMAL.png'
        assert not test_body(image).check_meta(), 'It is normal skill list'

    def test_find_not_full_level_skill_1(self):
        image = 'D:/project/AlasTest/tactical/SKILL_LEVEL_FIRST.png'
        assert TACTICAL_SKILL_LEVEL_1 == test_body(image).find_not_full_level_skill(load_image(image)), \
            'First skill is not full'

    def test_find_not_full_level_skill_2(self):
        image = 'D:/project/AlasTest/tactical/SKILL_LEVEL_NONE.png'
        assert test_body(image).find_not_full_level_skill(load_image(image)) is None, \
            'First skill is not full'

if __name__ == '__main__':
    unittest.main()
