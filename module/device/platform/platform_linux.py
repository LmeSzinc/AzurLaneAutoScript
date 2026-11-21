import re
import subprocess
import typing as t

from module.base.decorator import run_once
from module.base.timer import Timer
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
    def execute_wait(cls, command: t.List[str], timeout: float) -> int:
        """
        Execute a command and wait until it exits.

        Args:
            command: Command and arguments, executed without shell
            timeout: Seconds to wait

        Returns:
            int: Return code

        Raises:
            ExecuteFailed: If command failed to start or timeout
        """
        process = cls.execute(command)
        try:
            return process.wait(timeout=timeout)
        except subprocess.TimeoutExpired as e:
            logger.error(f'Execute timeout after {timeout}s: {command}')
            process.kill()
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
        # Import psutil on demand, it costs about 11ms and is only used here,
        # keeping it out of the startup path of the device stack
        import psutil

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
            # `waydroid session stop` returns after session stopped.
            # Wait for it, otherwise a following `session start` would be stopped as well.
            self.execute_wait([instance.path, 'session', 'stop'], timeout=60)
        else:
            raise EmulatorUnknown(f'Cannot stop an unknown emulator instance: {instance}')

    def _emulator_function_wrapper(self, func: callable):
        """
        Args:
            func (callable): _emulator_start or _emulator_stop

        Returns:
            bool: If success
        """
        try:
            func(self.emulator_instance)
            return True
        except (EmulatorUnknown, ExecuteFailed) as e:
            logger.error(e)
        except Exception as e:
            logger.exception(e)

        logger.error(f'Emulator function {func.__name__}() failed')
        return False

    def emulator_start_watch(self):
        """
        Wait until emulator is online, adb shell is available and azurlane package is found.

        Returns:
            bool: True if startup completed
                False if timeout
        """
        logger.hr('Emulator start', level=2)
        serial = self.emulator_instance.serial

        @run_once
        def show_online(m):
            logger.info(f'Emulator online: {m}')

        @run_once
        def show_ping(m):
            logger.info(f'Command ping: {m}')

        @run_once
        def show_package(m):
            logger.info(f'Found azurlane packages: {m}')

        interval = Timer(0.5).start()
        timeout = Timer(180).start()
        while 1:
            interval.wait()
            interval.reset()
            if timeout.reached():
                logger.warning('Emulator start timeout')
                return False

            # Check device connection
            # Waydroid is a network device, it won't show up until connected
            device = self.list_device().select(serial=serial).first_or_none()
            if device is None:
                self.adb_client.connect(serial)
                continue
            if device.status == 'offline':
                self.adb_client.disconnect(serial)
                self.adb_client.connect(serial)
                continue
            if device.status != 'device':
                continue
            show_online(device)

            # Check command availability
            try:
                pong = self.adb_shell(['echo', 'pong'])
            except Exception as e:
                logger.info(e)
                continue
            show_ping(pong)

            # Check azurlane package
            packages = self.list_known_packages(show_log=False)
            if not len(packages):
                continue
            show_package(packages)

            # All check passed
            break

        logger.info('Emulator start completed')
        return True

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
                if self.emulator_start_watch():
                    # Success
                    return True
                else:
                    # Start command was sent but emulator didn't come online, stop and start again
                    continue
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
