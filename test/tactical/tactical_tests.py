import sys
import unittest

from module.base.utils import load_image
from module.config.config import AzurLaneConfig
from module.device.debug_device import DebugDevice
from module.logger import logger
from module.tactical.assets import TACTICAL_SKILL_LEVEL_1, ADD_NEW_STUDENT, TACTICAL_SKILL_LEVEL_2, TACTICAL_META_SKILL
from module.tactical.tactical_class import RewardTacticalClass
from module.ui.page import page_tactical

sys.path.append('././')


class TestTactical(unittest.TestCase):
    default_config = AzurLaneConfig('alas', 'Tactical')
    logger.setLevel('DEBUG')

    # The first position is not empty
    def test_button_appear(self):
        image_location = 'D:/project/AlasTest/tactical/META.png'

        az = RewardTacticalClass(config=self.default_config,
                                 device=DebugDevice(image_location=image_location))
        az.image_file = load_image(image_location)
        self.assertTrue(az.appear(TACTICAL_META_SKILL, offset=(500, 20), interval=2))

    def test_demo(self):
        selected = None
        if selected:
            print(1)

    """
    Test select_first_ship()
    """

    # Select first ship
    def test_select_first_ship_success(self):
        image_location = [
            'D:/project/AlasTest/tactical/2.png',
            'D:/project/AlasTest/tactical/2-1.png',
            'D:/project/AlasTest/tactical/3.png'
        ]

        az = RewardTacticalClass(config=self.default_config,
                                 device=DebugDevice(image_location=image_location))
        self.assertTrue(az.select_first_ship())

    # Select first ship
    def test_select_first_ship_success_2(self):
        str = 'abcd ddd'
        print(str.replace(' ', ''))

    """
    Test find_not_full_level_skill 
    """

    # All not max, select first
    def test_find_not_full_level_skill_success(self):
        image_location = 'D:/project/AlasTest/tactical/3.png'

        az = RewardTacticalClass(config=self.default_config,
                                 device=DebugDevice(image_location=image_location))
        self.assertEqual(az.find_not_full_level_skill(load_image(image_location)), TACTICAL_SKILL_LEVEL_1)

    # Part max, select not max
    def test_find_not_full_level_skill_success_2(self):
        image_location = 'D:/project/AlasTest/tactical/11-1.png'

        az = RewardTacticalClass(config=self.default_config,
                                 device=DebugDevice(image_location=image_location))
        self.assertEqual(az.find_not_full_level_skill(load_image(image_location)), TACTICAL_SKILL_LEVEL_2)

    # All max, select None
    def test_find_not_full_level_skill_success_3(self):
        image_location = 'D:/project/AlasTest/tactical/12.png'

        az = RewardTacticalClass(config=self.default_config,
                                 device=DebugDevice(image_location=image_location))
        self.assertEqual(az.find_not_full_level_skill(load_image(image_location)), None)

    """
    Test whole process
    """

    def test_tactical_class_set(self):
        az = RewardTacticalClass(config='alas', task='Tactical')
        az.ui_ensure(page_tactical)


if __name__ == '__main__':
    unittest.main()
