import logging

from deploy.config import DeployConfig
from deploy.emulator import EmulatorConnect
from deploy.utils import *


class AdbManager(DeployConfig):
    @cached_property
    def adb(self):
        return self.filepath('AdbExecutable')

    def adb_install(self):
        hr0('Start ADB service')

        emulator = EmulatorConnect(adb=self.adb)
        if self.bool('ReplaceAdb'):
            hr1('Replace ADB')
            emulator.adb_replace()
        elif self.bool('AutoConnect'):
            hr1('ADB Connect')
            emulator.brute_force_connect()

        if self.bool('InstallUiautomator2'):
            hr1('Uiautomator2 Init')
            from uiautomator2.init import Initer
            import adbutils
            for device in adbutils.adb.iter_device():
                init = Initer(device, loglevel=logging.DEBUG)
                init.set_atx_agent_addr('127.0.0.1:7912')
                try:
                    init.install()
                except AssertionError:
                    print(f'AssertionError when installing uiautomator2 on device {device.serial}')
                    print('If you are using BlueStacks or LD player or WSA, '
                          'please enable ADB in the settings of your emulator')
                init._device.shell(["rm", "/data/local/tmp/minicap"])
                init._device.shell(["rm", "/data/local/tmp/minicap.so"])
