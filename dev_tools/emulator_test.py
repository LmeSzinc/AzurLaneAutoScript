import time

import numpy as np

from module.config.config import AzurLaneConfig
from module.device.device import Device


class EmulatorChecker(Device):
    def stress_test(self):
        record = []
        count = 0
        self._screenshot_adb()
        while 1:
            t0 = time.time()
            # self._screenshot_adb()
            self._screenshot_uiautomator2()
            # self._click_adb(1270, 360)
            # self._click_uiautomator2(1270, 360)

            cost = time.time() - t0
            record.append(cost)
            count += 1
            print(count, np.round(np.mean(record), 3), np.round(np.std(record), 3))


class Config:
    SERIAL = '127.0.0.1:62001'
    # SERIAL = '127.0.0.1:7555'
    # SERIAL = 'emulator-5554'
    # SERIAL = '127.0.0.1:21503'

    USE_ADB_SREENSHOT = False


az = EmulatorChecker(AzurLaneConfig().merge(Config()))
az.stress_test()
