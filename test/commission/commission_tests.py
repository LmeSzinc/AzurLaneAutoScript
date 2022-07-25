import sys
import unittest

from module.base.utils import load_image
from module.commission.commission import RewardCommission
from module.commission.commission import lines_detect
from module.config.config import AzurLaneConfig
from module.config.server import set_server
from module.device.device import Device

sys.path.append('././')


class TestCommission(unittest.TestCase):

    def test_commission_detect(self):
        # set server
        set_server('cn')

        # load image from disk
        file = r'D:/project/AlasTest/commission/COMMISSION_LIST.png'
        image = load_image(file)

        # construct test object
        config = AzurLaneConfig('alas')
        device = Device(config)
        rc = RewardCommission(config, device)
        commissions = rc._commission_detect(image)

        # execute
        lines_detect(image)

        # print result
        for commission in commissions:
            print(commission.name + ':' + commission.duration_hour)


if __name__ == '__main__':
    unittest.main()
