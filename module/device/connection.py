import os
import subprocess

import uiautomator2 as u2
from winreg import *

from module.config.config import AzurLaneConfig
from module.logger import logger


class Connection:
    _adb_binary = ''
    adb_binary_list = [
        r'.\adb\adb.exe',
        r'.\toolkit\Lib\site-packages\adbutils\binaries\adb.exe',
        r'.\python\Lib\site-packages\adbutils\binaries\adb.exe',
        '/usr/bin/adb'
    ]

    def __init__(self, config):
        """
        Args:
            config(AzurLaneConfig):
        """
        logger.hr('Device')
        self.config = config
        self.serial = str(self.config.Emulator_Serial)
        if "bluestacks4-hyperv" in self.serial:
            self.serial = self.find_bluestacks_hyperv(self.serial)

        self.device = self.connect(self.serial)
        # Set from 3min to 7days
        self.device.set_new_command_timeout(604800)
        # if self.config.DEVICE_SCREENSHOT_METHOD == 'aScreenCap':
        #     self._ascreencap_init()

    @staticmethod
    def find_bluestacks_hyperv(serial):
        """
        Find dynamic serial of Bluestacks4 Hyper-v Beta.

        Args:
            serial (str): 'bluestacks4-hyperv', 'bluestacks4-hyperv-2' for multi instance, and so on.

        Returns:
            str: 127.0.0.1:{port}
        """
        logger.info("Use Bluestacks4 Hyper-v Beta")
        if serial == "bluestacks4-hyperv":
            folder_name = "Android"
        else:
            folder_name = f"Android_{serial[19:]}"

        logger.info("Reading Realtime adb port")
        reg_root = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
        sub_dir = f"SOFTWARE\\BlueStacks_bgp64_hyperv\\Guests\\{folder_name}\\Config"
        bs_keys = OpenKey(reg_root, sub_dir)
        bs_keys_count = QueryInfoKey(bs_keys)[1]
        for i in range(bs_keys_count):
            key_name, key_value, key_type = EnumValue(bs_keys, i)
            if key_name == "BstAdbPort":
                logger.info(f"New adb port: {key_value}")
                serial = f"127.0.0.1:{key_value}"
                break

        CloseKey(bs_keys)
        CloseKey(reg_root)
        return serial

    @property
    def adb_binary(self):
        if self._adb_binary:
            return self._adb_binary

        # Try existing adb.exe
        for file in self.adb_binary_list:
            if os.path.exists(file):
                logger.attr('Adb_binary', file)
                self._adb_binary = file
                return file

        # Use adb.exe in system PATH
        file = 'adb.exe'
        logger.attr('Adb_binary', file)
        self._adb_binary = file
        return file

    def adb_command(self, cmd, serial=None):
        if serial:
            cmd = [self.adb_binary, '-s', serial] + cmd
        else:
            cmd = [self.adb_binary, '-s', self.serial] + cmd

        # Use shell=True to disable console window when using GUI.
        # Although, there's still a window when you stop running in GUI, which cause by gooey.
        # To disable it, edit gooey/gui/util/taskkill.py
        if self.adb_binary == '/usr/bin/adb':
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=False)
        else:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        return process.communicate(timeout=10)[0]

    def adb_shell(self, cmd, serial=None):
        cmd.insert(0, 'shell')
        return self.adb_command(cmd, serial)

    def adb_exec_out(self, cmd, serial=None):
        cmd.insert(0, 'exec-out')
        return self.adb_command(cmd, serial)

    def adb_forward(self, cmd, serial=None):
        cmd.insert(0, 'forward')
        return self.adb_command(cmd, serial)

    def adb_push(self, cmd, serial=None):
        cmd.insert(0, 'push')
        self.adb_command(cmd, serial)

    def _adb_connect(self, serial):
        if 'emulator' in serial:
            return True
        else:
            for _ in range(3):
                msg = self.adb_command(['connect', serial]).decode("utf-8").strip()
                logger.info(msg)
                if 'connected' in msg:
                    return True
            logger.warning(f'Failed to connect {serial} after 3 trial.')
            return False

    def connect(self, serial):
        """Connect to a device.

        Args:
            serial (str): device serial or device address.

        Returns:
            uiautomator2.UIAutomatorServer: Device.
        """
        self._adb_connect(serial)
        try:
            device = u2.connect(serial)
            return device
        except AssertionError:
            logger.warning('AssertionError when connecting emulator with uiautomator2.')
            logger.warning('If you are using BlueStacks, you need to enable ADB in the settings of your emulator.')

    def remove_minicap(self):
        """
        Force to delete minicap.

        `minicap` sends compressed images, which may cause detection errors.
        In most situation, uiautomator won't install minicap on emulators, but sometimes will.
        """
        logger.info('Removing minicap')
        self.adb_shell(["rm", "/data/local/tmp/minicap"])
        self.adb_shell(["rm", "/data/local/tmp/minicap.so"])
