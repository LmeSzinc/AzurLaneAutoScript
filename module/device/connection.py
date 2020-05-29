import subprocess

import requests
import uiautomator2 as u2

from module.config.config import AzurLaneConfig
from module.logger import logger


class Connection:
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
        self.check_screen_size()

    @staticmethod
    def adb_command(cmd, serial=None):
        if serial:
            cmd = ['adb', '-s', serial] + cmd
        else:
            cmd = ['adb'] + cmd

        # Use shell=True to disable console window when using GUI.
        # Although, there's still a window when you stop running in GUI, which cause by gooey.
        # To disable it, edit gooey/gui/util/taskkill.py
        result = subprocess.check_output(cmd, timeout=4, stderr=subprocess.STDOUT, shell=True)
        return result

    def adb_shell(self, cmd, serial=None):
        cmd.insert(0, 'shell')
        return self.adb_command(cmd, serial)

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
        device = u2.connect(serial)
        return device

    def disable_uiautomator2_auto_quit(self, port=7912, expire=300000):
        self.adb_command(['forward', 'tcp:%s' % port, 'tcp:%s' % port], serial=self.serial)
        requests.post('http://127.0.0.1:%s/newCommandTimeout' % port, data=str(expire))

    def check_screen_size(self):
        width, height = self.device.window_size()
        if height > width:
            width, height = height, width

        logger.attr('Screen_size', f'{width}x{height}')

        if width == 1280 and height == 720:
            return True
        else:
            logger.warning(f'Not supported screen size: {width}x{height}')
            logger.warning('Alas requires 1280x720')
            logger.hr('Script end')
            exit(1)
