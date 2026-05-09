import subprocess

from module.device.platform.emulator_linux import Emulator, EmulatorInstance, EmulatorManager
from module.device.platform.platform_base import PlatformBase
from module.logger import logger


class EmulatorUnknown(Exception):
    pass


class PlatformLinux(PlatformBase, EmulatorManager):
    @classmethod
    def execute(cls, command):
        """
        Args:
            command (str):

        Returns:
            subprocess.Popen:
        """
        logger.info(f'Execute: {command}')
        return subprocess.Popen(command, shell=True, close_fds=True, start_new_session=True)

    @classmethod
    def kill_process_by_regex(cls, regex: str) -> int:
        """
        Kill processes with cmdline matching the given regex.

        Args:
            regex:

        Returns:
            int: Number of processes killed
        """
        import os
        count = 0
        for pid in os.listdir('/proc'):
            if not pid.isdigit():
                continue
            try:
                cmdline_path = f'/proc/{pid}/cmdline'
                with open(cmdline_path, 'rb') as f:
                    cmdline = f.read().decode('utf-8', errors='replace')
                if regex in cmdline:
                    try:
                        os.kill(int(pid), 9)
                        count += 1
                        logger.info(f'Kill process: pid={pid}, cmdline={cmdline}')
                    except (PermissionError, ProcessLookupError):
                        pass
            except (FileNotFoundError, PermissionError, OSError):
                continue

        return count

    def _emulator_start(self, instance: EmulatorInstance):
        """
        Start a waydroid emulator instance.
        """
        if instance == Emulator.Waydroid:
            # Start waydroid container and session
            self.execute('waydroid container start')
            self.execute('waydroid session start')
        else:
            raise EmulatorUnknown(f'Cannot start an unknown emulator instance: {instance}')

    def _emulator_stop(self, instance: EmulatorInstance):
        """
        Stop a waydroid emulator instance.
        """
        if instance == Emulator.Waydroid:
            self.execute('waydroid session stop')
            self.execute('waydroid container stop')
        else:
            raise EmulatorUnknown(f'Cannot stop an unknown emulator instance: {instance}')

    def _emulator_function_wrapper(self, func):
        """
        Args:
            func: Function to call, must take instance as argument

        Returns:
            bool: If success
        """
        try:
            func(self.emulator_instance)
            return True
        except Exception as e:
            logger.error(e)
            return False

    def emulator_start(self):
        """
        Start the waydroid emulator until startup is complete.
        """
        logger.hr('Emulator start', level=1)
        for _ in range(3):
            # Stop
            if not self._emulator_function_wrapper(self._emulator_stop):
                return False
            # Start
            if self._emulator_function_wrapper(self._emulator_start):
                return True
            else:
                # Failed to start, stop and start again
                if self._emulator_function_wrapper(self._emulator_stop):
                    continue
                else:
                    return False

        logger.error('Failed to start emulator 3 times, stopped')
        return False

    def emulator_stop(self):
        """
        Stop the waydroid emulator.
        """
        logger.hr('Emulator stop', level=1)
        for _ in range(3):
            if self._emulator_function_wrapper(self._emulator_stop):
                return True
            else:
                if self._emulator_function_wrapper(self._emulator_start):
                    continue
                else:
                    return False

        logger.error('Failed to stop emulator 3 times, stopped')
        return False
