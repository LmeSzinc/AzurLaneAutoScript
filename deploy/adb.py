import logging

from deploy.config import DeployConfig
from deploy.emulator import EmulatorConnect
from deploy.logger import logger
from deploy.utils import *

IGNORE_SERIAL = [
    # Water-cooling display
    # https://github.com/LmeSzinc/AzurLaneAutoScript/issues/3412
    'HRBDFUN',
    # USB network card
    '1234567890ABCDEF',
]


def show_fix_tip(module):
    logger.info(f"""
    To fix this:
    1. Open console.bat
    2. Execute the following commands:
        pip uninstall -y {module}
        pip install --no-cache-dir {module}
    3. Re-open Alas.exe
    """)


class AdbManager(DeployConfig):
    @cached_property
    def adb(self):
        exe = self.filepath('AdbExecutable')
        if os.path.exists(exe):
            return exe

        logger.warning(f'AdbExecutable: {exe} does not exist, use `adb` instead')
        return 'adb'

    def adb_install(self):
        logger.hr('Start ADB service', 0)

        emulator = EmulatorConnect(adb=self.adb)
        if self.ReplaceAdb:
            logger.hr('Replace ADB', 1)
            emulator.adb_replace()
        elif self.AutoConnect:
            logger.hr('ADB Connect', 1)
            emulator.brute_force_connect()

        if False:
            logger.hr('Uiautomator2 Init', 1)
            try:
                import adbutils
                from uiautomator2 import init
            except ModuleNotFoundError as e:
                message = str(e)
                for module in ['apkutils2', 'progress']:
                    # ModuleNotFoundError: No module named 'apkutils2'
                    # ModuleNotFoundError: No module named 'progress.bar'
                    if module in message:
                        show_fix_tip(module)
                        exit(1)
                raise

            # Remove global proxies, or uiautomator2 will go through it
            for k in list(os.environ.keys()):
                if k.lower().endswith('_proxy'):
                    del os.environ[k]

            for device in adbutils.adb.iter_device():
                if device.serial in IGNORE_SERIAL:
                    continue
                logger.info(f'Init device {device}')
                initer = init.Initer(device, loglevel=logging.DEBUG)
                # MuMu X has no ro.product.cpu.abi, pick abi from ro.product.cpu.abilist
                if initer.abi not in ['x86_64', 'x86', 'arm64-v8a', 'armeabi-v7a', 'armeabi']:
                    initer.abi = initer.abis[0]
                # /bin/sh: getprop: not found
                if 'getprop' in initer.abi:
                    logger.warning(f'Cannot getprop from device {device}, result: {initer.abi}')
                    continue
                initer.set_atx_agent_addr('127.0.0.1:7912')

                for _ in range(2):
                    try:
                        initer.install()
                        break
                    except AssertionError:
                        logger.info(f'AssertionError when installing uiautomator2 on device {device.serial}')
                        logger.info('If you are using BlueStacks or LD player or WSA, '
                                    'please enable ADB in the settings of your emulator')
                        exit(1)
                    except ConnectionError:
                        if _ == 1:
                            raise
                        init.GITHUB_BASEURL = 'http://tool.appetizer.io/openatx'

                initer._device.shell(["rm", "/data/local/tmp/minicap"])
                initer._device.shell(["rm", "/data/local/tmp/minicap.so"])
