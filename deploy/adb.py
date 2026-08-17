from deploy.config import DeployConfig
from deploy.emulator import EmulatorConnect
from deploy.logger import logger
from deploy.utils import cached_property, os


class AdbManager(DeployConfig):
    @cached_property
    def adb(self):
        exe = self.filepath("AdbExecutable")
        if os.path.exists(exe):
            return exe

        logger.warning(f"AdbExecutable: {exe} does not exist, use `adb` instead")
        return "adb"

    def adb_install(self):
        logger.hr("Start ADB service", 0)

        emulator = EmulatorConnect(adb=self.adb)
        if self.ReplaceAdb:
            logger.hr("Replace ADB", 1)
            emulator.adb_replace()
        elif self.AutoConnect:
            logger.hr("ADB Connect", 1)
            emulator.brute_force_connect()
