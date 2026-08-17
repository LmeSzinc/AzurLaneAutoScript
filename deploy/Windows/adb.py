from deploy.Windows.emulator import EmulatorManager
from deploy.Windows.logger import Progress, logger


class AdbManager(EmulatorManager):
    def adb_install(self):
        logger.hr("Start ADB service", 0)

        if self.ReplaceAdb:
            logger.hr("Replace ADB", 1)
            self.adb_replace()
            Progress.AdbReplace()
        if self.AutoConnect:
            logger.hr("ADB Connect", 1)
            self.brute_force_connect()
            Progress.AdbConnect()
