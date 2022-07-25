import sys
import unittest

from module.config.config import AzurLaneConfig
from module.device.debug_device import DebugDevice
from module.tactical.assets import ADD_NEW_STUDENT
from module.tactical.tactical_class import RewardTacticalClass

sys.path.append('././')


class TestTactical(unittest.TestCase):
    default_config = AzurLaneConfig('alas', 'Tactical')

    def test_tactical_book_select(self):
        image_folder = 'D:/project/AlasTest/tactical/'

        az = RewardTacticalClass(config=self.default_config,
                                 device=DebugDevice(image_folder=image_folder))
        az._tactical_books_get()
        self.assertTrue(az.books is not None)
        for book in az.books:
            print(str(book.genre_str) + ':' + str(book.tier_str) + ':' + str(book.exp_value) + ':' + str(book.same_str))

    def test_add_new_student_ui_ensure(self):
        image_folder = 'D:/project/AlasTest/tactical/'

        az = RewardTacticalClass(config=self.default_config,
                                 device=DebugDevice(image_folder=image_folder))
        self.assertTrue(az.appear(ADD_NEW_STUDENT, offset=(20, 20), interval=2))

    def test_add_new_student_ui_ensure_and_click(self):
        image_folder = 'D:/project/AlasTest/tactical/'

        az = RewardTacticalClass(config=self.default_config,
                                 device=DebugDevice(image_folder=image_folder))
        self.assertTrue(az.appear_then_click(ADD_NEW_STUDENT, offset=(20, 20), interval=2))


if __name__ == '__main__':
    unittest.main()
