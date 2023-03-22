import ctypes
import subprocess
import typing as t

import psutil

from module.base.decorator import run_once
from module.base.timer import Timer
from module.device.connection import AdbDeviceWithStatus
from module.device.platform.platform_base import PlatformBase
from module.device.platform.windows_emulator import Emulator, EmulatorInstance, EmulatorManager
from module.logger import logger


class EmulatorUnknown(Exception):
    pass


def get_focused_window():
    return ctypes.windll.user32.GetForegroundWindow()


def set_focus_window(hwnd):
    ctypes.windll.user32.SetForegroundWindow(hwnd)


def minimize_window(hwnd):
    ctypes.windll.user32.ShowWindow(hwnd, 6)


def get_window_title(hwnd):
    """Returns the window title as a string."""
    textLenInCharacters = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
    stringBuffer = ctypes.create_unicode_buffer(
        textLenInCharacters + 1)  # +1 for the \0 at the end of the null-terminated string.
    ctypes.windll.user32.GetWindowTextW(hwnd, stringBuffer, textLenInCharacters + 1)
    return stringBuffer.value


def flash_window(hwnd, flash=True):
    ctypes.windll.user32.FlashWindow(hwnd, flash)


class PlatformWindows(PlatformBase, EmulatorManager):
    @staticmethod
    def execute(command):
        """
        Args:
            command (str):

        Returns:
            subprocess.Popen:
        """
        command = command.replace(r"\\", "/").replace("\\", "/").replace('"', '"')
        logger.info(f'Execute: {command}')
        return subprocess.Popen(command, close_fds=True)  # only work on Windows

    @staticmethod
    def taskkill(process):
        """
        Args:
            process (str, list[str]): Process name or a list of them

        Returns:
            subprocess.Popen:
        """
        if not isinstance(process, list):
            process = [process]
        return self.execute(f'taskkill /t /f /im ' + ''.join(process))

    @staticmethod
    def iter_running_emulator() -> t.Iterable[psutil.Process]:
        """
        This may cost some time.
        """
        for proc in psutil.process_iter():
            if Emulator.is_emulator(str(proc.name())):
                yield proc

    def find_running_emulator(self, instance: EmulatorInstance) -> t.Optional[psutil.Process]:
        for proc in self.iter_running_emulator():
            cmdline = [arg.replace('\\', '/').replace(r'\\', '/') for arg in proc.cmdline()]
            cmdline = ' '.join(cmdline)
            if instance.path in cmdline and instance.name in cmdline:
                return proc

        logger.warning(f'Cannot find a running emulator process with path={instance.path}, name={instance.name}')
        return None

    def emulator_kill_by_process(self, instance: EmulatorInstance) -> bool:
        """
        Kill a emulator by finding its process.

        Args:
            instance:

        Returns:
            bool: If success
        """
        proc = self.find_running_emulator(instance)
        if proc is not None:
            proc.kill()
            return True
        else:
            return False

    def _emulator_start(self, instance: EmulatorInstance):
        """
        Start a emulator without error handling
        """
        exe = instance.emulator.path
        if instance == Emulator.MumuPlayer:
            # NemuPlayer.exe
            self.execute(exe)
        if instance == Emulator.MumuPlayer9:
            # NemuPlayer.exe -m nemu-12.0-x64-default
            self.execute(f'{exe} -m {instance.name}')
        elif instance == Emulator.NoxPlayerFamily:
            # Nox.exe -clone:Nox_1
            self.execute(f'{exe} -clone:{instance.name}')
        elif instance == Emulator.BlueStacks5:
            # HD-Player.exe -instance Pie64
            self.execute(f'{exe} -instance {instance.name}')
        elif instance == Emulator.BlueStacks4:
            # BlueStacks\Client\Bluestacks.exe -vmname Android_1
            self.execute(f'{exe} -vmname {instance.name}')
        else:
            raise EmulatorUnknown(f'Cannot start an unknown emulator instance: {instance}')

    def _emulator_stop(self, instance: EmulatorInstance):
        """
        Stop a emulator without error handling
        """
        exe = instance.emulator.path
        if instance == Emulator.MumuPlayer:
            # taskkill /t /f /im NemuHeadless.exe NemuPlayer.exe NemuSvc.exe
            self.taskkill(['NemuHeadless.exe', 'NemuPlayer.exe', 'NemuSvc.exe'])
        elif instance == Emulator.MumuPlayer9:
            # Kill by process
            self.emulator_kill_by_process(instance)
        elif instance == Emulator.NoxPlayerFamily:
            # Nox.exe -clone:Nox_1 -quit
            self.execute(f'{exe} -clone:{instance.name} -quit')
        else:
            raise EmulatorUnknown(f'Cannot stop an unknown emulator instance: {instance}')

    def _emulator_function_wrapper(self, func):
        """
        Args:
            func (callable): _emulator_start or _emulator_stop

        Returns:
            bool: If success
        """
        try:
            func(self.emulator_instance)
            return True
        except OSError as e:
            msg = str(e)
            # OSError: [WinError 740] 请求的操作需要提升。
            if 'WinError 740' in msg:
                logger.error('To start/stop MumuAppPlayer, ALAS needs to be run as administrator')
        except Exception as e:
            logger.error(e)

        logger.error(f'Emulator function {func.__name__}() failed')
        return False

    def emulator_start_watch(self):
        """
        Returns:
            bool: True if startup completed
                False if timeout
        """
        current_window = get_focused_window()
        serial = self.emulator_instance.serial
        logger.info(f'Current window: {current_window}')

        def adb_connect():
            m = self.adb_client.connect(self.serial)
            if 'connected' in m:
                # Connected to 127.0.0.1:59865
                # Already connected to 127.0.0.1:59865
                return False
            elif '(10061)' in m:
                # cannot connect to 127.0.0.1:55555:
                # No connection could be made because the target machine actively refused it. (10061)
                return False
            else:
                return True

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
        timeout = Timer(300).start()
        new_window = 0
        while 1:
            interval.wait()
            interval.reset()
            if timeout.reached():
                logger.warning(f'Emulator start timeout')
                return False

            # Check emulator window showing up
            # logger.info([get_focused_window(), get_window_title(get_focused_window())])
            if current_window != 0 and new_window == 0:
                new_window = get_focused_window()
                if current_window != new_window:
                    logger.info(f'New window showing up: {new_window}, focus back')
                    set_focus_window(current_window)
                else:
                    new_window = 0

            # Check device connection
            devices = self.list_device().select(serial=serial)
            # logger.info(devices)
            if devices:
                device: AdbDeviceWithStatus = devices.first_or_none()
                if device.status == 'device':
                    # Emulator online
                    pass
                if device.status == 'offline':
                    self.adb_client.disconnect(serial)
                    adb_connect()
                    continue
            else:
                # Try to connect
                adb_connect()
                continue
            show_online(devices.first_or_none())

            # Check command availability
            try:
                pong = self.adb_shell(['echo', 'pong'])
            except Exception as e:
                logger.info(e)
                continue
            show_ping(pong)

            # Check azuelane package
            packages = self.list_azurlane_packages(show_log=False)
            if len(packages):
                pass
            else:
                continue
            show_package(packages)

            # All check passed
            break

        if new_window != 0 and new_window != current_window:
            logger.info(f'Minimize new window: {new_window}')
            minimize_window(new_window)
        if current_window:
            logger.info(f'De-flash current window: {current_window}')
            flash_window(current_window, flash=False)
        if new_window:
            logger.info(f'Flash new window: {new_window}')
            flash_window(new_window, flash=True)
        logger.info('Emulator start completed')
        return True

    def emulator_start(self):
        for _ in range(3):
            # Stop
            if not self._emulator_function_wrapper(self._emulator_stop):
                return False
            # Start
            if self._emulator_function_wrapper(self._emulator_start):
                # Success
                self.emulator_start_watch()
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
        return self._emulator_function_wrapper(self._emulator_stop)


if __name__ == '__main__':
    self = PlatformWindows('alas')
    self.emulator_start()
