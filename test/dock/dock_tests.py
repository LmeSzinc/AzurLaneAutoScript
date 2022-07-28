import sys
import unittest

from module.combat.level import LevelOcr
from module.config.config import AzurLaneConfig
from module.device.debug_device import DebugDevice
from module.retire.dock import Dock, CARD_GRIDS, CARD_LEVEL_GRIDS

sys.path.append('././')


class TestDock(unittest.TestCase):
    default_config = AzurLaneConfig('alas', 'Dock')

    def test_dock_empty(self):
        image_location = 'D:/project/AlasTest/dock/DOCK_1.png'
        az = Dock(config=self.default_config,
                  device=DebugDevice(image_location=image_location))

        level_grids = CARD_LEVEL_GRIDS
        card_grids = CARD_GRIDS
        level_ocr = LevelOcr(CARD_LEVEL_GRIDS[(0, 1)],
                             name='DOCK_LEVEL_OCR', threshold=64)
        list_level = level_ocr.ocr(az.device.image)
        print(list_level)


if __name__ == '__main__':
    unittest.main()
