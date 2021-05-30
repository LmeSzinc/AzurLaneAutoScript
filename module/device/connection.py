import os
import subprocess

import requests
import uiautomator2 as u2

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
        self.serial = str(self.config.SERIAL)
        self.device = self.connect(self.serial)
        self.disable_uiautomator2_auto_quit()
        # if self.config.DEVICE_SCREENSHOT_METHOD == 'aScreenCap':
        #     self._ascreencap_init()

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
        if serial.startswith('127.0.0.1'):
            msg = self.adb_command(['connect', serial]).decode("utf-8")
            if msg.startswith('unable'):
                logger.error('Unable to connect %s' % serial)
                exit(1)
            else:
                logger.info(msg.strip())

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

    def disable_uiautomator2_auto_quit(self, port=7912, expire=3000000):
        self.adb_forward(['tcp:%s' % port, 'tcp:%s' % port])
        requests.post('http://127.0.0.1:%s/newCommandTimeout' % port, data=str(expire))
