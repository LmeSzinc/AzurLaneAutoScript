import os
import shutil
import subprocess
import typing as t

# module/device/platform/emulator_base.py
# module/device/platform/emulator_windows.py
# Will be used in Alas Easy Install, they shouldn't import any Alas modules.
from module.device.platform.emulator_base import (
    EmulatorBase,
    EmulatorInstanceBase,
    EmulatorManagerBase,
    remove_duplicated_path,
)
from module.device.platform.utils import cached_property


def get_waydroid_serial() -> str:
    """
    Need to make sure waydroid is running

    Returns:
        waydroid IP address
    """

    """
    $ waydroid --version
    1.4.3
    $ waydroid status
    Session:	RUNNING
    Container:	RUNNING
    Vendor type:	MAINLINE
    IP address:	192.168.240.112
    Session user:	docker(1000)
    Wayland display:	wayland-0
    """

    waydroid_cmd = shutil.which('waydroid')
    if waydroid_cmd is None:
        return ''

    try:
        waydroid_status = subprocess.check_output([waydroid_cmd, 'status'], text=True)
    except (PermissionError, OSError):
        return ''

    ip_address_line = None
    for line in waydroid_status.splitlines():
        if line.startswith('IP address:'):
            ip_address_line = line
            break
    if ip_address_line is None or ip_address_line.endswith('UNKNOWN'):
        return ''
    ip_address = ip_address_line.removeprefix('IP address:').strip()
    return f'{ip_address}:5555'


class EmulatorInstance(EmulatorInstanceBase):
    @cached_property
    def emulator(self):
        """
        Returns:
            Emulator:
        """
        return Emulator(self.path)


class Emulator(EmulatorBase):
    @classmethod
    def path_to_type(cls, path: str) -> str:
        """
        Args:
            path: Path to .exe file, case insensitive

        Returns:
            str: Emulator type, such as Emulator.NoxPlayer
        """
        folder, exe = os.path.split(path)
        folder, dir1 = os.path.split(folder)
        folder, dir2 = os.path.split(folder)
        exe = exe.lower()
        dir1 = dir1.lower()
        dir2 = dir2.lower()

        if exe == 'waydroid':
            return cls.Waydroid

        return ''

    def iter_instances(self):
        """
        Yields:
            EmulatorInstance: Emulator instances found in this emulator
        """
        if self == Emulator.Waydroid:
            # Waydroid has no multi instances, on 5555 only
            serial=get_waydroid_serial()
            if serial:
                yield EmulatorInstance(
                    serial=serial,
                    name='',
                    path=self.path,
                )


class EmulatorManager(EmulatorManagerBase):
    @staticmethod
    def get_install_emulator() -> list[str]:
        """
        Args:
            path (str): f'SOFTWARE\\leidian\\ldplayer'
            key (str): 'InstallDir'

        Returns:
            list[str]: Installation dir or None
        """
        result = []

        exe = shutil.which('waydroid')
        if exe is not None:
            result.append(exe)

        return result

    @staticmethod
    def iter_running_emulator():
        """
        Yields:
            str: Path to emulator executables, may contains duplicate values
        """
        try:
            import psutil
        except ModuleNotFoundError:
            return
        # Since this is a one-time-usage, we access psutil._psplatform.Process directly
        # to bypass the call of psutil.Process.is_running().
        # This only costs about 0.017s.
        for pid in psutil.pids():
            proc = psutil._psplatform.Process(pid)
            try:
                exe = proc.cmdline()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                # psutil.AccessDenied
                # NoSuchProcess: process no longer exists (pid=xxx)
                continue

            if len(exe) == 0:
                continue
            if len(exe) >= 1 and Emulator.is_emulator(exe[0]):
                yield exe[0]
            # /usr/bin/python3 /usr/bin/waydroid show-full-ui
            if len(exe) >= 2 and Emulator.is_emulator(exe[1]):
                yield exe[1]

    @cached_property
    def all_emulators(self) -> t.List[Emulator]:
        """
        Get all emulators installed on current computer.
        """
        exe = set([])

        for file in EmulatorManager.get_install_emulator():
            if Emulator.is_emulator(file) and os.path.exists(file):
                exe.add(file)

        # Running
        for file in EmulatorManager.iter_running_emulator():
            if os.path.exists(file):
                exe.add(file)

        # De-redundancy
        exe = [Emulator(path).path for path in exe if Emulator.is_emulator(path)]
        exe = [Emulator(path) for path in remove_duplicated_path(exe)]
        return exe

    @cached_property
    def all_emulator_instances(self) -> t.List[EmulatorInstance]:
        """
        Get all emulator instances installed on current computer.
        """
        instances = []
        for emulator in self.all_emulators:
            instances += list(emulator.iter_instances())

        instances: t.List[EmulatorInstance] = sorted(instances, key=lambda x: str(x))
        return instances


if __name__ == '__main__':
    self = EmulatorManager()
    for emu in self.all_emulator_instances:
        print(emu)
