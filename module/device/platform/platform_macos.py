import subprocess

from module.base.decorator import run_once
from module.base.timer import Timer
from module.device.connection import AdbDeviceWithStatus
from module.device.platform.emulator_macos import Emulator, EmulatorInstance, EmulatorManager
from module.device.platform.platform_base import PlatformBase
from module.exception import EmulatorNotRunningError
from module.logger import logger


class EmulatorUnknown(Exception):
    pass


class PlatformMacOS(PlatformBase, EmulatorManager):
    @classmethod
    def execute(cls, command):
        """
        Args:
            command (list[str]):

        Returns:
            subprocess.Popen:
        """
        logger.info(f'Execute: {" ".join(command)}')
        # `start_new_session` to avoid emulator getting tree-killed when Alas gets killed
        return subprocess.Popen(command, start_new_session=True)

    def adb_connect(self, wait_device=True):
        """
        Raise EmulatorNotRunningError when BlueStacks Air is not running.

        ADB on macOS reports `Connection refused`, which is not handled by
        the Windows error code in Connection.adb_connect.
        """
        result = super().adb_connect(wait_device=wait_device)
        if result is False:
            instance = self.emulator_instance
            if instance == Emulator.BlueStacks5:
                logger.warning('No such device exists, please restart the emulator or set a correct serial')
                raise EmulatorNotRunningError
        return result

    def _emulator_start(self, instance: EmulatorInstance):
        """
        Start a emulator without error handling
        """
        if instance == Emulator.BlueStacks5:
            # BlueStacks.app/Contents/MacOS/BlueStacks
            self.execute([instance.path])
        else:
            raise EmulatorUnknown(f'Cannot start an unknown emulator instance: {instance}')

    def _emulator_function_wrapper(self, func: callable):
        """
        Args:
            func (callable): _emulator_start

        Returns:
            bool: If success
        """
        try:
            func(self.emulator_instance)
            return True
        except EmulatorUnknown as e:
            logger.error(e)
        except Exception as e:
            logger.exception(e)

        logger.error(f'Emulator function {func.__name__}() failed')
        return False

    def emulator_start_watch(self):
        """
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
                logger.warning(f'Emulator start timeout')
                return False

            # Check device connection
            devices = self.list_device().select(serial=serial)
            if devices:
                device: AdbDeviceWithStatus = devices.first_or_none()
                if device.status == 'device':
                    # Emulator online
                    pass
                if device.status == 'offline':
                    self.adb_client.disconnect(serial)
                    self.adb_client.connect(serial)
                    continue
            else:
                # Try to connect
                self.adb_client.connect(serial)
                continue
            show_online(devices.first_or_none())

            # Check command availability
            try:
                pong = self.adb_shell(['echo', 'pong'])
            except Exception as e:
                logger.info(e)
                continue
            show_ping(pong)

            # Check azurlane package
            packages = self.list_known_packages(show_log=False)
            if len(packages):
                pass
            else:
                continue
            show_package(packages)

            # All check passed
            break

        logger.info('Emulator start completed')
        return True

    def emulator_start(self):
        logger.hr('Emulator start', level=1)
        if self._emulator_function_wrapper(self._emulator_start):
            if self.emulator_start_watch():
                return True

        logger.error('Failed to start emulator')
        return False


if __name__ == '__main__':
    self = PlatformMacOS('alas')
    d = self.emulator_instance
    print(d)
