import codecs
import os
import re
import typing as t
import winreg
from dataclasses import dataclass

# module/device/platform/emulator_base.py
# module/device/platform/emulator_windows.py
# Will be used in Alas Easy Install, they shouldn't import any Alas modules.
from module.device.platform.emulator_base import EmulatorBase, EmulatorInstanceBase, EmulatorManagerBase, \
    remove_duplicated_path
from module.device.platform.utils import cached_property, iter_folder


@dataclass
class RegValue:
    name: str
    value: str
    typ: int


def list_reg(reg) -> t.List[RegValue]:
    """
    List all values in a reg key
    """
    rows = []
    index = 0
    try:
        while 1:
            value = RegValue(*winreg.EnumValue(reg, index))
            index += 1
            rows.append(value)
    except OSError:
        pass
    return rows


def list_key(reg) -> t.List[RegValue]:
    """
    List all values in a reg key
    """
    rows = []
    index = 0
    try:
        while 1:
            value = winreg.EnumKey(reg, index)
            index += 1
            rows.append(value)
    except OSError:
        pass
    return rows


def abspath(path):
    return os.path.abspath(path).replace('\\', '/')


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
        if exe == 'nox.exe':
            if dir2 == 'nox':
                return cls.NoxPlayer
            elif dir2 == 'nox64':
                return cls.NoxPlayer64
            else:
                return cls.NoxPlayer
        if exe in ['bluestacks.exe', 'bluestacksgp.exe']:
            if dir1 in ['bluestacks', 'bluestacks_cn', 'bluestackscn']:
                return cls.BlueStacks4
            elif dir1 in ['bluestacks_nxt', 'bluestacks_nxt_cn']:
                return cls.BlueStacks5
            else:
                return cls.BlueStacks4
        if exe == 'hd-player.exe':
            if dir1 in ['bluestacks', 'bluestacks_cn']:
                return cls.BlueStacks4
            elif dir1 in ['bluestacks_nxt', 'bluestacks_nxt_cn']:
                return cls.BlueStacks5
            else:
                return cls.BlueStacks5
        if exe == 'dnplayer.exe':
            if dir1 == 'ldplayer':
                return cls.LDPlayer3
            elif dir1 == 'ldplayer4':
                return cls.LDPlayer4
            elif dir1 == 'ldplayer9':
                return cls.LDPlayer9
            else:
                return cls.LDPlayer3
        if exe == 'nemuplayer.exe':
            if dir2 == 'nemu':
                return cls.MuMuPlayer
            elif dir2 == 'nemu9':
                return cls.MuMuPlayerX
            else:
                return cls.MuMuPlayer
        if exe in ['mumuplayer.exe', 'mumunxmain.exe']:
            return cls.MuMuPlayer12
        if exe == 'memu.exe':
            return cls.MEmuPlayer

        return ''

    @staticmethod
    def multi_to_single(exe: str):
        """
        Convert a string that might be a multi-instance manager to its single instance executable.

        Args:
            exe (str): Path to emulator executable

        Yields:
            str: Path to emulator executable
        """
        if 'HD-MultiInstanceManager.exe' in exe:
            yield exe.replace('HD-MultiInstanceManager.exe', 'HD-Player.exe')
            yield exe.replace('HD-MultiInstanceManager.exe', 'Bluestacks.exe')
        elif 'MultiPlayerManager.exe' in exe:
            yield exe.replace('MultiPlayerManager.exe', 'Nox.exe')
        elif 'dnmultiplayer.exe' in exe:
            yield exe.replace('dnmultiplayer.exe', 'dnplayer.exe')
        elif 'NemuMultiPlayer.exe' in exe:
            yield exe.replace('NemuMultiPlayer.exe', 'NemuPlayer.exe')
        elif 'MuMuMultiPlayer.exe' in exe:
            yield exe.replace('MuMuMultiPlayer.exe', 'MuMuPlayer.exe')
        elif 'MuMuManager.exe' in exe:
            yield exe.replace('MuMuManager.exe', 'MuMuPlayer.exe')
        elif 'MEmuConsole.exe' in exe:
            yield exe.replace('MEmuConsole.exe', 'MEmu.exe')
        else:
            yield exe

    @staticmethod
    def single_to_console(exe: str):
        """
        Convert a string that might be a single instance executable to its console.

        Args:
            exe (str): Path to emulator executable

        Returns:
            str: Path to emulator console
        """
        if 'MuMuPlayer.exe' in exe:
            return exe.replace('MuMuPlayer.exe', 'MuMuManager.exe')
        # MuMuPlayer12 5.0
        elif 'MuMuPlayer.exe' in exe:
            return exe.replace('MuMuNxMain.exe', 'MuMuManager.exe')
        elif 'LDPlayer.exe' in exe:
            return exe.replace('LDPlayer.exe', 'ldconsole.exe')
        elif 'dnplayer.exe' in exe:
            return exe.replace('dnplayer.exe', 'ldconsole.exe')
        elif 'Bluestacks.exe' in exe:
            return exe.replace('Bluestacks.exe', 'bsconsole.exe')
        elif 'MEmu.exe' in exe:
            return exe.replace('MEmu.exe', 'memuc.exe')
        else:
            return exe

    @staticmethod
    def vbox_file_to_serial(file: str) -> str:
        """
        Args:
            file: Path to vbox file

        Returns:
            str: serial such as `127.0.0.1:5555`
        """
        regex = re.compile('<*?hostport="(.*?)".*?guestport="5555"/>')
        try:
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f.readlines():
                    # <Forwarding name="port2" proto="1" hostip="127.0.0.1" hostport="62026" guestport="5555"/>
                    res = regex.search(line)
                    if res:
                        return f'127.0.0.1:{res.group(1)}'
            return ''
        except FileNotFoundError:
            return ''

    def iter_instances(self):
        """
        Yields:
            EmulatorInstance: Emulator instances found in this emulator
        """
        if self == Emulator.NoxPlayerFamily:
            # ./BignoxVMS/{name}/{name}.vbox
            for folder in self.list_folder('./BignoxVMS', is_dir=True):
                for file in iter_folder(folder, ext='.vbox'):
                    serial = Emulator.vbox_file_to_serial(file)
                    if serial:
                        yield EmulatorInstance(
                            serial=serial,
                            name=os.path.basename(folder),
                            path=self.path,
                        )
        elif self == Emulator.BlueStacks5:
            # Get UserDefinedDir, where BlueStacks stores data
            folder = None
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\BlueStacks_nxt") as reg:
                    folder = winreg.QueryValueEx(reg, 'UserDefinedDir')[0]
            except FileNotFoundError:
                pass
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\BlueStacks_nxt_cn") as reg:
                    folder = winreg.QueryValueEx(reg, 'UserDefinedDir')[0]
            except FileNotFoundError:
                pass
            if not folder:
                return
            # Read {UserDefinedDir}/bluestacks.conf
            try:
                with open(self.abspath('./bluestacks.conf', folder), encoding='utf-8') as f:
                    content = f.read()
            except FileNotFoundError:
                return
            # bst.instance.Nougat64.adb_port="5555"
            emulators = re.findall(r'bst.instance.(\w+).status.adb_port="(\d+)"', content)
            for emulator in emulators:
                yield EmulatorInstance(
                    serial=f'127.0.0.1:{emulator[1]}',
                    name=emulator[0],
                    path=self.path,
                )
        elif self == Emulator.BlueStacks4:
            # ../Engine/Android
            regex = re.compile(r'^Android')
            for folder in self.list_folder('./Engine/ProgramData/Engine', is_dir=True):
                folder = os.path.basename(folder)
                res = regex.match(folder)
                if not res:
                    continue
                # Serial from BlueStacks4 are not static, they get increased on every emulator launch
                # Assume all use 127.0.0.1:5555
                yield EmulatorInstance(
                    serial=f'127.0.0.1:5555',
                    name=folder,
                    path=self.path
                )
        elif self == Emulator.LDPlayerFamily:
            # ./vms/leidian0
            regex = re.compile(r'^leidian(\d+)$')
            for folder in self.list_folder('./vms', is_dir=True):
                folder = os.path.basename(folder)
                res = regex.match(folder)
                if not res:
                    continue
                # LDPlayer has no forward port config in .vbox file
                # Ports are auto increase, 5555, 5557, 5559, etc
                port = int(res.group(1)) * 2 + 5555
                yield EmulatorInstance(
                    serial=f'127.0.0.1:{port}',
                    name=folder,
                    path=self.path
                )
        elif self == Emulator.MuMuPlayer:
            # MuMu has no multi instances, on 7555 only
            yield EmulatorInstance(
                serial='127.0.0.1:7555',
                name='',
                path=self.path,
            )
        elif self == Emulator.MuMuPlayerX:
            # vms/nemu-12.0-x64-default
            for folder in self.list_folder('../vms', is_dir=True):
                for file in iter_folder(folder, ext='.nemu'):
                    serial = Emulator.vbox_file_to_serial(file)
                    if serial:
                        yield EmulatorInstance(
                            serial=serial,
                            name=os.path.basename(folder),
                            path=self.path,
                        )
        elif self == Emulator.MuMuPlayer12:
            # vms/MuMuPlayer-12.0-0
            for folder in self.list_folder('../vms', is_dir=True):
                for file in iter_folder(folder, ext='.nemu'):
                    serial = Emulator.vbox_file_to_serial(file)
                    name = os.path.basename(folder)
                    if serial:
                        yield EmulatorInstance(
                            serial=serial,
                            name=name,
                            path=self.path,
                        )
                    # Fix for MuMu12 v4.0.4, default instance of which has no forward record in vbox config
                    else:
                        instance = EmulatorInstance(
                            serial=serial,
                            name=name,
                            path=self.path,
                        )
                        if instance.MuMuPlayer12_id:
                            instance.serial = f'127.0.0.1:{16384 + 32 * instance.MuMuPlayer12_id}'
                            yield instance
        elif self == Emulator.MEmuPlayer:
            # ./MemuHyperv VMs/{name}/{name}.memu
            for folder in self.list_folder('./MemuHyperv VMs', is_dir=True):
                for file in iter_folder(folder, ext='.memu'):
                    serial = Emulator.vbox_file_to_serial(file)
                    if serial:
                        yield EmulatorInstance(
                            serial=serial,
                            name=os.path.basename(folder),
                            path=self.path,
                        )

    def iter_adb_binaries(self) -> t.Iterable[str]:
        """
        Yields:
            str: Filepath to adb binaries found in this emulator
        """
        if self == Emulator.NoxPlayerFamily:
            exe = self.abspath('./nox_adb.exe')
            if os.path.exists(exe):
                yield exe
        if self == Emulator.MuMuPlayerFamily:
            # From MuMu9\emulator\nemu9\EmulatorShell
            # to MuMu9\emulator\nemu9\vmonitor\bin\adb_server.exe
            exe = self.abspath('../vmonitor/bin/adb_server.exe')
            if os.path.exists(exe):
                yield exe

        # All emulators have adb.exe
        exe = self.abspath('./adb.exe')
        if os.path.exists(exe):
            yield exe


class EmulatorManager(EmulatorManagerBase):
    @staticmethod
    def iter_user_assist():
        """
        Get recently executed programs in UserAssist
        https://github.com/forensicmatt/MonitorUserAssist

        Yields:
            str: Path to emulator executables, may contains duplicate values
        """
        path = r'Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist'
        # {XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}\xxx.exe
        regex_hash = re.compile(r'{.*}')
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as reg:
                folders = list_key(reg)
        except FileNotFoundError:
            return

        for folder in folders:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, f'{path}\\{folder}\\Count') as reg:
                    for key in list_reg(reg):
                        key = codecs.decode(key.name, 'rot-13')
                        # Skip those with hash
                        if regex_hash.search(key):
                            continue
                        for file in Emulator.multi_to_single(key):
                            yield file
            except FileNotFoundError:
                # FileNotFoundError: [WinError 2] 系统找不到指定的文件。
                # Might be a random directory without "Count" subdirectory
                continue

    @staticmethod
    def iter_mui_cache():
        """
        Iter emulator executables that has ever run.
        http://what-when-how.com/windows-forensic-analysis/registry-analysis-windows-forensic-analysis-part-8/
        https://3gstudent.github.io/%E6%B8%97%E9%80%8F%E6%8A%80%E5%B7%A7-Windows%E7%B3%BB%E7%BB%9F%E6%96%87%E4%BB%B6%E6%89%A7%E8%A1%8C%E8%AE%B0%E5%BD%95%E7%9A%84%E8%8E%B7%E5%8F%96%E4%B8%8E%E6%B8%85%E9%99%A4

        Yields:
            str: Path to emulator executable, may contains duplicate values
        """
        path = r'Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\MuiCache'
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as reg:
                rows = list_reg(reg)
        except FileNotFoundError:
            return

        regex = re.compile(r'(^.*\.exe)\.')
        for row in rows:
            res = regex.search(row.name)
            if not res:
                continue
            for file in Emulator.multi_to_single(res.group(1)):
                yield file

    @staticmethod
    def get_install_dir_from_reg(path, key):
        """
        Args:
            path (str): f'SOFTWARE\\leidian\\ldplayer'
            key (str): 'InstallDir'

        Returns:
            str: Installation dir or None
        """
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as reg:
                root = winreg.QueryValueEx(reg, key)[0]
                return root
        except FileNotFoundError:
            pass
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as reg:
                root = winreg.QueryValueEx(reg, key)[0]
                return root
        except FileNotFoundError:
            pass

        return None

    @staticmethod
    def iter_uninstall_registry():
        """
        Iter emulator uninstaller from registry.

        Yields:
            str: Path to uninstall exe file
        """
        known_uninstall_registry_path = [
            r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall',
            r'Software\Microsoft\Windows\CurrentVersion\Uninstall'
        ]
        known_emulator_registry_name = [
            'Nox',
            'Nox64',
            'BlueStacks',
            'BlueStacks_nxt',
            'BlueStacks_cn',
            'BlueStacks_nxt_cn',
            'LDPlayer',
            'LDPlayer4',
            'LDPlayer9',
            'leidian',
            'leidian4',
            'leidian9',
            'Nemu',
            'Nemu9',
            'MuMuPlayer',
            'MuMuPlayer-12.0',
            'MuMu Player 12.0',
            'MEmu',
        ]
        for path in known_uninstall_registry_path:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as reg:
                    software_list = list_key(reg)
            except FileNotFoundError:
                continue
            for software in software_list:
                if software not in known_emulator_registry_name:
                    continue
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, f'{path}\\{software}') as software_reg:
                        uninstall = winreg.QueryValueEx(software_reg, 'UninstallString')[0]
                except FileNotFoundError:
                    continue
                if not uninstall:
                    continue
                # UninstallString is like:
                # C:\Program Files\BlueStacks_nxt\BlueStacksUninstaller.exe -tmp
                # "E:\ProgramFiles\Microvirt\MEmu\uninstall\uninstall.exe" -u
                # Extract path in ""
                res = re.search('"(.*?)"', uninstall)
                uninstall = res.group(1) if res else uninstall
                yield uninstall

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
                exe = exe[0].replace(r'\\', '/').replace('\\', '/')
            except (psutil.AccessDenied, psutil.NoSuchProcess, IndexError, OSError):
                # psutil.AccessDenied
                # NoSuchProcess: process no longer exists (pid=xxx)
                # OSError: [WinError 87] 参数错误。: '(originated from ReadProcessMemory)'
                continue

            if Emulator.is_emulator(exe):
                yield exe

    @cached_property
    def all_emulators(self) -> t.List[Emulator]:
        """
        Get all emulators installed on current computer.
        """
        exe = set([])

        # MuiCache
        for file in EmulatorManager.iter_mui_cache():
            if Emulator.is_emulator(file) and os.path.exists(file):
                exe.add(file)

        # UserAssist
        for file in EmulatorManager.iter_user_assist():
            if Emulator.is_emulator(file) and os.path.exists(file):
                exe.add(file)

        # LDPlayer install path
        for path in [r'SOFTWARE\leidian\ldplayer',
                     r'SOFTWARE\leidian\ldplayer9']:
            ld = self.get_install_dir_from_reg(path, 'InstallDir')
            if ld:
                ld = abspath(os.path.join(ld, './dnplayer.exe'))
                if Emulator.is_emulator(ld) and os.path.exists(ld):
                    exe.add(ld)

        # Uninstall registry
        for uninstall in EmulatorManager.iter_uninstall_registry():
            # Find emulator executable from uninstaller
            for file in iter_folder(abspath(os.path.dirname(uninstall)), ext='.exe'):
                if Emulator.is_emulator(file) and os.path.exists(file):
                    exe.add(file)
            # Find from parent directory
            for file in iter_folder(abspath(os.path.join(os.path.dirname(uninstall), '../')), ext='.exe'):
                if Emulator.is_emulator(file) and os.path.exists(file):
                    exe.add(file)
            # MuMu specific directory
            for file in iter_folder(abspath(os.path.join(os.path.dirname(uninstall), 'EmulatorShell')), ext='.exe'):
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
