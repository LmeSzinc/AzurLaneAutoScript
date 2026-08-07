import filecmp
import logging
import socket
import subprocess

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

    @staticmethod
    def _adb_server_version():
        host = '127.0.0.1'
        try:
            port = int(os.environ.get('ANDROID_ADB_SERVER_PORT', 5037))
        except ValueError:
            port = 5037

        # AdbClient starts the server on connection refused, so probe the socket first.
        try:
            with socket.create_connection((host, port), timeout=0.5):
                pass
        except OSError:
            return None

        try:
            from adbutils import AdbClient, AdbError
            return AdbClient(host, port).server_version()
        except (AdbError, OSError, ValueError):
            return None

    @staticmethod
    def _adb_binary_version(adb):
        try:
            process = subprocess.run(
                [adb, 'version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=10,
                shell=False,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
            )
        except (OSError, subprocess.TimeoutExpired):
            return None

        result = re.search(rb'Android Debug Bridge version 1\.0\.(\d+)', process.stdout)
        return int(result.group(1)) if result else None

    @classmethod
    def _adb_server_compatible(cls, adb, check_version):
        server_version = cls._adb_server_version()
        if server_version is None:
            return False
        if not check_version:
            return True

        binary_version = cls._adb_binary_version(adb)
        if binary_version is None:
            return True
        if server_version != binary_version:
            logger.info(
                f'ADB server version {server_version} differs from binary version {binary_version}'
            )
            return False
        return True

    @staticmethod
    def _adb_replacement_required(emulator, adb):
        for instance in emulator.emulators:
            for binary in instance.adb_binary:
                try:
                    if os.path.exists(binary) and not filecmp.cmp(adb, binary, shallow=True):
                        return True
                except OSError:
                    return True
        return False

    @staticmethod
    def _adb_install(adb, replace_adb, auto_connect, emulator=None):
        logger.hr('Start ADB service', 0)

        if emulator is None:
            emulator = EmulatorConnect(adb=adb)
        if replace_adb:
            logger.hr('Replace ADB', 1)
            emulator.adb_replace()
        elif auto_connect:
            logger.hr('ADB Connect', 1)
            emulator.brute_force_connect()

    def adb_install(self):
        self._adb_install(
            adb=self.adb,
            replace_adb=self.ReplaceAdb,
            auto_connect=self.AutoConnect,
        )

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

    @classmethod
    def adb_install_on_demand(cls, adb, replace_adb, auto_connect):
        """
        Initialize ADB once it is required by an Android device.
        A file lock prevents concurrent Alas instances from replacing ADB at the same time.
        """
        from filelock import FileLock

        lock = FileLock(os.path.abspath('./config/adb_install.lock'))
        with lock:
            emulator = EmulatorConnect(adb=adb)
            replacement_required = replace_adb and cls._adb_replacement_required(emulator, adb)
            if not replacement_required and cls._adb_server_compatible(
                    adb=adb, check_version=replace_adb or auto_connect):
                logger.info('ADB service is already available, skip startup')
                return
            cls._adb_install(
                adb=adb,
                replace_adb=replace_adb,
                auto_connect=auto_connect,
                emulator=emulator,
            )
