import asyncio
import filecmp
import os
import shutil
import sys
import typing as t
from dataclasses import dataclass

from deploy.Windows.alas import AlasManager
from deploy.Windows.logger import logger
from deploy.Windows.utils import cached_property

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


@dataclass
class DataAdbDevice:
    serial: str
    status: str


class EmulatorManager(AlasManager):
    @cached_property
    def emulator_manager(self):
        from module.device.platform.emulator_windows import EmulatorManager
        return EmulatorManager()

    def adb_kill(self):
        # Just kill it, because some adb don't obey.
        logger.hr('Kill all known ADB', level=2)
        for proc in self.iter_process_by_names([
            # Most emulator use this
            'adb.exe',
            # NoxPlayer 夜神模拟器
            'nox_adb.exe',
            # MumuPlayer MuMu模拟器
            'adb_server.exe',
            # Bluestacks 蓝叠模拟器
            'HD-Adb.exe'
        ]):
            logger.info(proc)
            self.kill_process(proc)

    def adb_devices(self):
        """
        Returns:
            list[DataAdbDevice]: Connected devices in adb
        """
        logger.hr('Adb deivces', level=2)
        result = self.subprocess_execute([self.adb, 'devices'])
        devices = []
        for line in result.replace('\r\r\n', '\n').replace('\r\n', '\n').split('\n'):
            if line.startswith('List') or '\t' not in line:
                continue
            serial, status = line.split('\t')
            device = DataAdbDevice(
                serial=serial,
                status=status,
            )
            devices.append(device)
            logger.info(device)
        return devices

    def brute_force_connect(self):
        """
        Brute-force connect all available emulator instances
        """
        devices = self.adb_devices()

        # Disconnect offline devices
        for device in devices:
            if device.status == 'offline':
                self.subprocess_execute([self.adb, 'disconnect', device.serial])

        # Get serial
        list_serial = self.emulator_manager.all_emulator_serials

        logger.hr('Brute force connect', level=2)

        async def _connect(serial):
            try:
                await asyncio.create_subprocess_exec(self.adb, 'connect', serial)
            except Exception as e:
                logger.info(e)

        async def connect():
            await asyncio.gather(
                *[_connect(serial) for serial in list_serial]
            )

        asyncio.run(connect())

        return self.adb_devices()

    @staticmethod
    def adb_path_to_backup(adb, new_backup=True):
        """
        Args:
            adb (str): Filepath to an adb binary
            new_backup (bool): True to return a new backup path,
                False to return an existing backup

        Returns:
            str: Filepath to its backup file
        """
        for n in range(10):
            backup = f'{adb}.bak{n}' if n else f'{adb}.bak'
            if os.path.exists(backup):
                if new_backup:
                    continue
                else:
                    return backup
            else:
                if new_backup:
                    return backup
                else:
                    continue

        # Too many backups, override the first one
        return f'{adb}.bak'

    def iter_adb_to_replace(self) -> t.Iterable[str]:
        for adb in self.emulator_manager.all_adb_binaries:
            if filecmp.cmp(adb, self.adb, shallow=True):
                logger.info(f'{adb} is same as {self.adb}, skip')
                continue
            else:
                yield adb

    def adb_replace(self):
        """
        Backup the adb in emulator folder to xxx.bak, replace it with your adb.
        `adb kill-server` must be called before replacing.
        """
        replace = list(self.iter_adb_to_replace())
        if not replace:
            logger.info('No need to replace')
            return

        self.adb_kill()
        for adb in replace:
            logger.info(f'Replacing {adb}')
            bak = self.adb_path_to_backup(adb, new_backup=True)
            logger.info(f'{adb} -----> {bak}')
            shutil.move(adb, bak)
            logger.info(f'{self.adb} -----> {adb}')
            shutil.copy(self.adb, adb)

    def adb_recover(self):
        """
        Revert `adb_replace()`
        """
        for adb in self.emulator_manager.all_adb_binaries:
            logger.info(f'Recovering {adb}')
            bak = self.adb_path_to_backup(adb, new_backup=False)
            if os.path.exists(bak):
                logger.info(f'Delete {adb}')
                if os.path.exists(adb):
                    os.remove(adb)
                logger.info(f'{bak} -----> {adb}')
                shutil.move(bak, adb)
            else:
                logger.info('No backup available, skip')
                continue


if __name__ == '__main__':
    os.chdir(os.path.join(os.path.dirname(__file__), '../../'))
    self = EmulatorManager()
    self.brute_force_connect()
