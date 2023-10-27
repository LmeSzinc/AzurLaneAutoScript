import asyncio
import filecmp
import os
import re
import shutil
import subprocess
import winreg

from deploy.logger import logger
from deploy.utils import cached_property

asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


class VirtualBoxEmulator:
    UNINSTALL_REG = "SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall"
    UNINSTALL_REG_2 = "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall"

    def __init__(self, name, root_path, adb_path, vbox_path, vbox_name):
        """
        Args:
            name (str): Emulator name in windows uninstall list.
            root_path (str): Relative path from uninstall.exe to emulator installation folder.
            adb_path (str, list[str]): Relative path to adb.exe. List of str if there are multiple adb in emulator.
            vbox_path (str): Relative path to virtual box folder.
            vbox_name (str): Regular Expression to match the name of .vbox file.
        """
        self.name = name
        self.root_path = root_path
        self.adb_path = adb_path if isinstance(adb_path, list) else [adb_path]
        self.vbox_path = vbox_path
        self.vbox_name = vbox_name

    @cached_property
    def root(self):
        """
        Returns:
            str: Root installation folder of emulator.

        Raises:
            FileNotFoundError: If emulator not installed.
        """
        if self.name == 'LDPlayer4':
            root = self.get_install_dir_from_reg('SOFTWARE\\leidian\\ldplayer', 'InstallDir')
            if root is not None:
                return root
        if self.name == 'LDPlayer9':
            root = self.get_install_dir_from_reg('SOFTWARE\\leidian\\ldplayer9', 'InstallDir')
            if root is not None:
                return root

        try:
            reg = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, f'{self.UNINSTALL_REG}\\{self.name}', 0)
        except FileNotFoundError:
            reg = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, f'{self.UNINSTALL_REG_2}\\{self.name}', 0)
        res = winreg.QueryValueEx(reg, 'UninstallString')[0]

        file = re.search('"(.*?)"', res)
        file = file.group(1) if file else res
        root = os.path.abspath(os.path.join(os.path.dirname(file), self.root_path))
        return root

    def get_install_dir_from_reg(self, path, key):
        """
        Args:
            path (str): f'SOFTWARE\\leidian\\ldplayer'
            key (str): 'InstallDir'

        Returns:
            str: Installation dir or None
        """
        try:
            reg = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0)
            root = winreg.QueryValueEx(reg, key)[0]
            if os.path.exists(root):
                return root
        except FileNotFoundError:
            pass
        try:
            reg = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0)
            root = winreg.QueryValueEx(reg, key)[0]
            if os.path.exists(root):
                return root
        except FileNotFoundError:
            pass

        return None

    @cached_property
    def adb_binary(self):
        return [os.path.abspath(os.path.join(self.root, a)) for a in self.adb_path]

    @cached_property
    def adb_backup(self):
        files = []
        for adb in self.adb_binary:
            for n in range(10):
                backup = f'{adb}.bak{n}' if n else f'{adb}.bak'
                if os.path.exists(backup):
                    continue
                else:
                    files.append(backup)
                    break
        return files

    @cached_property
    def serial(self):
        """
        Returns:
            list[str]: Such as ['127.0.0.1:62001', '127.0.0.1:62025']
        """
        vbox = []
        for path, folders, files in os.walk(os.path.join(self.root, self.vbox_path)):
            for file in files:
                if re.match(self.vbox_name, file):
                    file = os.path.join(path, file)
                    vbox.append(file)

        serial = []
        for file in vbox:
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f.readlines():
                    # <Forwarding name="port2" proto="1" hostip="127.0.0.1" hostport="62026" guestport="5555"/>
                    res = re.search('<*?hostport="(.*?)".*?guestport="5555"/>', line)
                    if res:
                        serial.append(f'127.0.0.1:{res.group(1)}')

        return serial

    def adb_replace(self, adb):
        """
        Backup the adb in emulator folder to xxx.bak, replace it with your adb.
        Need to call `adb kill-server` before replacing.

        Args:
            adb (str): Absolute path to adb.exe
        """
        for ori, bak in zip(self.adb_binary, self.adb_backup):
            logger.info(f'Replacing {ori}')
            if os.path.exists(ori):
                if filecmp.cmp(adb, ori, shallow=True):
                    logger.info(f'{adb} is same as {ori}, skip')
                else:
                    logger.info(f'{ori} -----> {bak}')
                    shutil.move(ori, bak)
                    logger.info(f'{adb} -----> {ori}')
                    shutil.copy(adb, ori)
            else:
                logger.info(f'{ori} not exists, skip')

    def adb_recover(self):
        """ Revert adb replacement """
        for ori in self.adb_binary:
            logger.info(f'Recovering {ori}')
            bak = f'{ori}.bak'
            if os.path.exists(bak):
                logger.info(f'Delete {ori}')
                if os.path.exists(ori):
                    os.remove(ori)
                logger.info(f'{bak} -----> {ori}')
                shutil.move(bak, ori)
            else:
                logger.info(f'Not exists {bak}, skip')


# NoxPlayer 夜神模拟器
nox_player = VirtualBoxEmulator(
    name="Nox",
    root_path=".",
    adb_path=["./adb.exe", "./nox_adb.exe"],
    vbox_path="./BignoxVMS",
    vbox_name='.*.vbox$'
)
nox_player_64 = VirtualBoxEmulator(
    name="Nox64",
    root_path=".",
    adb_path=["./adb.exe", "./nox_adb.exe"],
    vbox_path="./BignoxVMS",
    vbox_name='.*.vbox$'
)
# LDPlayer 雷电模拟器
ld_player = VirtualBoxEmulator(
    name="LDPlayer",
    root_path=".",
    adb_path="./adb.exe",
    vbox_path="./vms",
    vbox_name='.*.vbox$'
)
ld_player_4 = VirtualBoxEmulator(
    name="LDPlayer4",
    root_path=".",
    adb_path="./adb.exe",
    vbox_path="./vms",
    vbox_name='.*.vbox$'
)
ld_player_9 = VirtualBoxEmulator(
    name="LDPlayer9",
    root_path=".",
    adb_path="./adb.exe",
    vbox_path="./vms",
    vbox_name='.*.vbox$'
)
# MemuPlayer 逍遥模拟器
memu_player = VirtualBoxEmulator(
    name="MEmu",
    root_path="../",
    adb_path="./adb.exe",
    vbox_path="./MemuHyperv VMs",
    vbox_name='.*.memu$'
)
# MumuPlayer MuMu模拟器
mumu_player = VirtualBoxEmulator(
    name="Nemu",
    root_path=".",
    adb_path="./vmonitor/bin/adb_server.exe",
    vbox_path="./vms",
    vbox_name='.*.nemu$'
)


class EmulatorConnect:
    SUPPORTED_EMULATORS = [
        nox_player,
        nox_player_64,
        ld_player,
        ld_player_4,
        ld_player_9,
        memu_player,
        mumu_player
    ]

    def __init__(self, adb='adb.exe'):
        self.adb_binary = adb

    def _execute(self, cmd, timeout=10, output=True):
        """
        Returns:
            Object: Stdout(str) of cmd if output,
                    return code(int) of cmd if not output.
        """
        if not output:
            cmd.extend(['>nul', '2>nul'])
        logger.info(' '.join(cmd))
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            ret_code = process.returncode
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            ret_code = 1
            logger.info(f'TimeoutExpired, stdout={stdout}, stderr={stderr}')
        if output:
            return stdout
        else:
            return ret_code

    @cached_property
    def emulators(self):
        """
        Returns:
            list: List of installed emulators on current computer.
        """
        emulators = []
        for emulator in self.SUPPORTED_EMULATORS:
            try:
                serial = emulator.serial
                emulators.append(emulator)
            except FileNotFoundError:
                continue
            if len(serial):
                logger.info(f'Emulator {emulator.name} found, instances: {serial}')

        return emulators

    def devices(self):
        """
        Returns:
            list[str]: Connected devices in adb
        """
        result = self._execute([self.adb_binary, 'devices']).decode()
        devices = []
        for line in result.replace('\r\r\n', '\n').replace('\r\n', '\n').split('\n'):
            if line.startswith('List') or '\t' not in line:
                continue
            serial, status = line.split('\t')
            if status == 'device':
                devices.append(serial)

        logger.info(f'Devices: {devices}')
        return devices

    def adb_kill(self):
        # self._execute([self.adb_binary, 'devices'])
        # self._execute([self.adb_binary, 'kill-server'])

        # Just kill it, because some adb don't obey.
        logger.info('Kill all known ADB')
        for exe in [
            # Most emulator use this
            'adb.exe',
            # NoxPlayer 夜神模拟器
            'nox_adb.exe',
            # MumuPlayer MuMu模拟器
            'adb_server.exe',
            # Bluestacks 蓝叠模拟器
            'HD-Adb.exe'
        ]:
            ret_code = self._execute(['taskkill', '/f', '/im', exe], output=False)
            if ret_code == 0:
                logger.info(f'Task {exe} killed')
            elif ret_code == 128:
                logger.info(f'Task {exe} not found')
            else:
                logger.info(f'Error occurred when killing task {exe}, return code {ret_code}')

    @cached_property
    def serial(self):
        """
        Returns:
            list[str]: All available emulator serial on current computer.
        """
        serial = ['127.0.0.1:7555']
        for emulator in self.emulators:
            serial += emulator.serial
            for s in emulator.serial:
                ip, port = s.split(':')
                port = int(port) - 1
                if 5554 <= int(port) < 5600:
                    serial.append(f'emulator-{port}')

        return serial

    def brute_force_connect(self):
        """ Brute-force connect all available emulator instances """
        self.devices()

        async def connect():
            await asyncio.gather(
                *[asyncio.create_subprocess_exec(self.adb_binary, 'connect', serial) for serial in self.serial]
            )

        asyncio.run(connect())

        return self.devices()

    def adb_replace(self, adb=None):
        """
        Different version of ADB will kill each other when starting.
        Chinese emulators (NoxPlayer, LDPlayer, MemuPlayer, MuMuPlayer) use their own adb,
        instead of the one in system PATH, so when they start they kill the adb.exe Alas is using.
        Replacing the ADB in emulator is the simplest way to solve this.

        Args:
            adb (str): Absolute path to adb.exe
        """
        self.adb_kill()
        for emulator in self.emulators:
            emulator.adb_replace(adb if adb is not None else self.adb_binary)
        self.brute_force_connect()

    def adb_recover(self):
        """ Revert adb replacement """
        self.adb_kill()
        for emulator in self.emulators:
            emulator.adb_recover()
        self.brute_force_connect()


if __name__ == '__main__':
    emu = EmulatorConnect()
    logger.info(emu.brute_force_connect())
