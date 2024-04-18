import subprocess
import sys

from module.device.platform.emulator_base import EmulatorBase
from module.device.platform.emulator_linux import EmulatorManager
from module.device.platform.platform_base import PlatformBase
from module.logger import logger


class PlatformLinux(PlatformBase, EmulatorManager):

    def execute(cls, command):
        """
        Args:
            command (str):

        Returns:
            True/False
        """
        command = command.replace(r"\\", "/").replace("\\", "/").replace('"', '"')
        logger.info(f'Execute: {command}')
        return subprocess.run(command, shell=True, close_fds=True).returncode == 0


    def emulator_start(self):
        """
        Start a emulator, until startup completed.
        - Retry is required.
        - Using bored sleep to wait startup is forbidden.
        """
        if self.emulator_info.emulator != EmulatorBase.CustomEmulator:
            logger.warning(f'Current platform {sys.platform} does not support emulator_start of {self.emulator_info.emulator}, skip')
            return

        self.custom_emulator_start()

    def emulator_stop(self):
        """
        Stop a emulator.
        """
        if self.emulator_info.emulator != EmulatorBase.CustomEmulator:
            logger.warning(f'Current platform {sys.platform} does not support emulator_stop of {self.emulator_info.emulator}, skip')
            return

        self.custom_emulator_stop()

