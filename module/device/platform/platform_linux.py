import re
import subprocess
import typing as t

import psutil

from module.device.platform.emulator_linux import Emulator, EmulatorInstance, EmulatorManager
from module.device.platform.platform_base import PlatformBase
from module.logger import logger


class EmulatorUnknown(Exception):
    pass


class ExecuteFailed(Exception):
    pass


class PlatformLinux(PlatformBase, EmulatorManager):
    @classmethod
    def execute(cls, command: t.List[str]) -> subprocess.Popen:
        """
        Args:
            command: Command and arguments, executed without shell

        Returns:
            subprocess.Popen:

        Raises:
            ExecuteFailed: If command failed to start
        """
        logger.info(f'Execute: {command}')
        try:
            # `start_new_session` to avoid emulator getting tree-killed when Alas gets killed
            return subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                start_new_session=True,
            )
        except (FileNotFoundError, PermissionError, OSError, ValueError) as e:
            logger.error(f'Failed to execute {command}: {e}')
            raise ExecuteFailed(str(e)) from e

    @classmethod
    def kill_process_by_regex(cls, regex: str) -> int:
        """
        Kill processes with cmdline match the given regex.

        Args:
            regex:

        Returns:
            int: Number of processes killed
        """
        count = 0

        for proc in psutil.process_iter(['cmdline']):
            cmdline = ' '.join(proc.info.get('cmdline') or [])
            if not cmdline or not re.search(regex, cmdline):
                continue
            try:
                proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.warning(f'Failed to kill process: {cmdline}, {e}')
                continue
            logger.info(f'Kill process: {cmdline}')
            count += 1

        return count

    def _emulator_start(self, instance: EmulatorInstance):
        """
        Start a waydroid emulator instance.
        """
        if instance == Emulator.Waydroid:
            self.execute([instance.path, 'session', 'start'])
        else:
            raise EmulatorUnknown(f'Cannot start an unknown emulator instance: {instance}')

    def _emulator_stop(self, instance: EmulatorInstance):
        """
        Stop a waydroid emulator instance.
        """
        if instance == Emulator.Waydroid:
            self.execute([instance.path, 'session', 'stop'])
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
        except (EmulatorUnknown, ExecuteFailed) as e:
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
