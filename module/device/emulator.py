import os
import re
import winreg
import subprocess
from sys import platform

from adbutils.errors import AdbError

from deploy.emulator import VirtualBoxEmulator
from module.base.decorator import cached_property
from module.device.connection import Connection
from module.exception import RequestHumanTakeover, EmulatorNotRunningError
from module.logger import logger


class EmulatorInstance(VirtualBoxEmulator):

    def __init__(self, name, root_path, emu_path, vbox_path=None, vbox_name=None, kill_para=None, multi_para=None):
        """
        Args:
            name (str): Emulator name in windows uninstall list.
            root_path (str): Relative path from uninstall.exe to emulator installation folder.
            emu_path (str): Relative path to executable simulator file.
            vbox_path (str): Relative path to virtual box folder.
            vbox_name (str): Regular Expression to match the name of .vbox file.
            kill_para (str): Parameters required by kill emulator.
            multi_para (str): Parameters required by start multi open emulator,
            #id will be replaced with the real ID.
        """
        super().__init__(
            name=name,
            root_path=root_path,
            adb_path=None,
            vbox_path=vbox_path,
            vbox_name=vbox_name,
        )
        self.emu_path = emu_path
        self.kill_para = kill_para
        self.multi_para = multi_para

    @cached_property
    def id_and_serial(self):
        """
        Returns:
            list[str, str]: List of multi_id and serial.
        """
        vbox = []
        for path, folders, files in os.walk(os.path.join(self.root, self.vbox_path)):
            for file in files:
                if re.match(self.vbox_name, file):
                    file = os.path.join(path, file)
                    vbox.append(file)

        serial = []
        for file in vbox:
            with open(file, 'r') as f:
                for line in f.readlines():
                    # <Forwarding name="port2" proto="1" hostip="127.0.0.1" hostport="62026" guestport="5555"/>
                    res = re.search('<*?hostport="(.*?)".*?guestport="5555"/>', line)
                    if res:
                        serial.append([os.path.basename(file).split(".")[0], f'127.0.0.1:{res.group(1)}'])

        return serial


class BluestacksInstance(EmulatorInstance):
    @cached_property
    def root(self):
        try:
            return super().root
        except FileNotFoundError:
            self.name = 'BlueStacks_nxt_cn'
            return super().root

    @cached_property
    def id_and_serial(self):
        try:
            reg = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\BlueStacks_nxt")
        except FileNotFoundError:
            reg = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\BlueStacks_nxt_cn")
        directory = winreg.QueryValueEx(reg, 'UserDefinedDir')[0]

        with open(os.path.join(directory, 'bluestacks.conf'), encoding='utf-8') as f:
            content = f.read()
        emulators = re.findall(r'bst.instance.(\w+).status.adb_port="(\d+)"', content)
        serial = []
        for emulator in emulators:
            serial.append([emulator[0], f'127.0.0.1:{emulator[1]}'])
        return serial


class EmulatorManager(Connection):
    pid = None

    SUPPORTED_EMULATORS = {
        'nox_player': EmulatorInstance(
            name="Nox",
            root_path=".",
            emu_path="./Nox.exe",
            vbox_path="./BignoxVMS",
            vbox_name='.*.vbox$',
            kill_para='-quit',
            multi_para='-clone:#id',
        ),
        'mumu_player': EmulatorInstance(
            name="Nemu",
            root_path=".",
            emu_path="./EmulatorShell/NemuPlayer.exe",
            vbox_path="./vms",
            vbox_name='.*.nemu$',
        ),
        'bluestacks_player_5': BluestacksInstance(
            name='BlueStacks_nxt',
            root_path='.',
            emu_path='./HD-Player.exe',
            multi_para='--instance #id',
        ),
    }

    def detect_emulator(self, serial, emulator=None):
        """
        Args:
            serial (str):
            emulator (EmulatorInstance):
        Returns:
            list[EmulatorInstance, str]:Emulator and multi_id
        """
        if emulator is None:
            logger.info('Detect emulator from all emulators installed')
            emulators = []
            for emulator in self.SUPPORTED_EMULATORS.values():
                try:
                    serials = emulator.id_and_serial
                    for cur_serial in serials:
                        if cur_serial[1] == serial:
                            emulators.append([emulator, cur_serial[0]])
                except FileNotFoundError:
                    pass

            logger.info('Detected emulators :')
            for emulator in emulators:
                logger.info(f'Name: {emulator[0].name}, Multi_id: {emulator[1]}')

            if len(emulators) == 1 or emulators[0][0] == self.SUPPORTED_EMULATORS['mumu_player']:
                logger.info('Find the only emulator, using it')
                return emulators[0][0], emulators[0][1]
            elif len(emulators) == 0:
                logger.warning('The emulator corresponding to serial is not found, '
                               'please check the setting or use custom command')
                raise RequestHumanTakeover
            else:
                logger.warning('Multiple emulators with the same serial have been found, '
                               'please select one manually or use custom command')
                raise RequestHumanTakeover

        else:
            try:
                logger.info(f'Detect emulator from {emulator.name}')
                serials = emulator.id_and_serial
                for cur_serial in serials:
                    if cur_serial[1] == serial:
                        logger.info('Find the only emulator, using it')
                        return emulator, cur_serial[0]
            except FileNotFoundError:
                logger.warning('The emulator corresponding to serial is not found, '
                               'please check the setting or use custom command')
                raise RequestHumanTakeover

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
        return subprocess.Popen(command)  # only work on Windows

    def adb_connect(self, serial):
        try:
            return super(EmulatorManager, self).adb_connect(serial)
        except EmulatorNotRunningError:
            if self.config.RestartEmulator_LaunchMode != 'do_not_use' \
                    and self.emulator_restart(kill=False):
                return True
            raise RequestHumanTakeover

    def detect_emulator_status(self, serial):
        devices = self.list_device()
        for device in devices:
            if device.serial == serial:
                return device.status
        return 'offline'

    def emulator_start(self, serial, emulator=None, multi_id=None, path=None):
        """
        Args:
            serial (str): Expected serial after simulator starts successfully.
            emulator (EmulatorInstance): Emulator to start.
            multi_id (str): Emulator ID used by multi open emulator.
            path (str): Customized path and parameters of the simulator to start.
        Return:
            bool: If start successful.
        """
        if path is not None:
            command = path
        else:
            command = os.path.abspath(os.path.join(emulator.root, emulator.emu_path))
            if multi_id is not None and emulator.multi_para is not None:
                command += " " + emulator.multi_para.replace("#id", multi_id)

        for _ in range(3):
            logger.info('Start emulator')
            pipe = self.execute(command)
            self.pid = pipe.pid
            self.sleep(20)

            for __ in range(20):
                if pipe.poll() is not None:
                    break
                try:
                    if super().adb_connect(serial):
                        self.sleep(5)
                        # Wait until emulator start completely
                        return True
                except EmulatorNotRunningError:
                    continue
                self.sleep(5)
        logger.warning('Emulator start failed for 3 times, please check your settings')
        raise RequestHumanTakeover

    def emulator_kill(self, serial, emulator=None, multi_id=None, path=None):
        """
        Args:
            serial (str): Expected serial after simulator starts successfully.
            emulator (EmulatorInstance): Emulator to start.
            multi_id (str): Emulator ID used by multi open emulator.
            path (str): Customized path and parameters of the simulator to start.
        Return:
            bool: If kill successful.
        """

        if emulator == self.SUPPORTED_EMULATORS['mumu_player']:
            # It is MuMu's fault, Alas is not to blame
            return self.emulator_kill(serial,
                                      path='taskkill /f /im NemuHeadless.exe /im NemuPlayer.exe /im NemuSvc.exe')

        if path is not None:
            command = path
        else:
            command = os.path.abspath(os.path.join(emulator.root, emulator.emu_path))
            if multi_id is not None and emulator.multi_para is not None:
                command += " " + emulator.multi_para.replace("#id", multi_id)

            if emulator.kill_para is not None:
                command += " " + emulator.kill_para
            elif self.pid is not None:
                command = f'taskkill /pid {self.pid} /f /t'
            else:
                command = f'taskkill /im {os.path.basename(emulator.emu_path)} /f /t'

        for _ in range(3):
            logger.info('Kill emulator')

            if emulator == self.SUPPORTED_EMULATORS['bluestacks_player_5']:
                try:
                    self.adb_command(['reboot', '-p'], timeout=20)
                    if self.detect_emulator_status(serial) == 'offline':
                        self.pid = None
                        return True
                except AdbError:
                    pass
            else:
                pipe = self.execute(command)
                self.sleep(5)

                for __ in range(10):
                    if pipe.poll() is not None:
                        if self.detect_emulator_status(serial) == 'offline':
                            self.pid = None
                            return True
                        continue
                    if self.detect_emulator_status(serial) == 'offline':
                        self.pid = None
                        return True
                    self.sleep(2)
        logger.warning('Emulator kill failed for 3 times, please check your settings')
        raise RequestHumanTakeover

    def emulator_restart(self, kill=True):
        serial = self.serial
        emulator = None
        multi_id = None
        start_path = None
        kill_path = None
        if self.config.RestartEmulator_LaunchMode == 'do_not_use':
            return False
        if platform != 'win32':
            logger.warning('Function of restart simulator only works under Windows platform')
            return False
        logger.hr('Emulator restart')
        if self.config.RestartEmulator_LaunchMode == 'auto':
            emulator, multi_id = self.detect_emulator(serial)
        elif self.config.RestartEmulator_LaunchMode == 'custom':
            start_path = self.config.RestartEmulator_CustomStartFilter
            kill_path = self.config.RestartEmulator_CustomKillFilter
        else:
            emulator = self.SUPPORTED_EMULATORS[self.config.RestartEmulator_LaunchMode]
            emulator, multi_id = self.detect_emulator(serial, emulator)

        if kill and not self.emulator_kill(serial, emulator, multi_id, kill_path):
            return False
        return self.emulator_start(serial, emulator, multi_id, start_path)
