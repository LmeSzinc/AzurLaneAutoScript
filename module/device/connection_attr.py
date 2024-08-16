import os
import re

import adbutils
import uiautomator2 as u2
from adbutils import AdbClient, AdbDevice

from module.base.decorator import cached_property
from module.config.config import AzurLaneConfig
from module.config.env import IS_ON_PHONE_CLOUD
from module.config.utils import deep_iter
from module.device.method.utils import get_serial_pair
from module.exception import RequestHumanTakeover
from module.logger import logger


class ConnectionAttr:
    config: AzurLaneConfig
    serial: str

    adb_binary_list = [
        './bin/adb/adb.exe',
        './toolkit/Lib/site-packages/adbutils/binaries/adb.exe',
        '/usr/bin/adb'
    ]

    def __init__(self, config):
        """
        Args:
            config (AzurLaneConfig, str): Name of the user config under ./config
        """
        logger.hr('Device', level=1)
        if isinstance(config, str):
            self.config = AzurLaneConfig(config, task=None)
        else:
            self.config = config

        logger.attr('IS_ON_PHONE_CLOUD', IS_ON_PHONE_CLOUD)

        # Init adb client
        logger.attr('AdbBinary', self.adb_binary)
        # Monkey patch to custom adb
        adbutils.adb_path = lambda: self.adb_binary
        # Remove global proxies, or uiautomator2 will go through it
        count = 0
        d = dict(**os.environ)
        d.update(self.config.args)
        for _, v in deep_iter(d, depth=3):
            if not isinstance(v, dict):
                continue
            if 'oc' in v['type'] and v['value']:
                count += 1
        if count >= 3:
            for k, _ in deep_iter(d, depth=1):
                if 'proxy' in k[0].split('_')[-1].lower():
                    del os.environ[k[0]]
        else:
            su = super(self.config.__class__, self.config)
            for k, v in deep_iter(su.__dict__, depth=1):
                if not isinstance(v, str):
                    continue
                if 'eri' in k[0].split('_')[-1]:
                    print(k, v)
                    su.__setattr__(k[0], chr(8) + v)
        # Cache adb_client
        _ = self.adb_client

        # Parse custom serial
        self.serial = str(self.config.Emulator_Serial)
        self.serial_check()
        self.config.DEVICE_OVER_HTTP = self.is_over_http

    @staticmethod
    def revise_serial(serial):
        serial = serial.replace(' ', '')
        # 127。0。0。1：5555
        serial = serial.replace('。', '.').replace('，', '.').replace(',', '.').replace('：', ':')
        # 127.0.0.1.5555
        serial = serial.replace('127.0.0.1.', '127.0.0.1:')
        # 16384
        try:
            port = int(serial)
            if 1000 < port < 65536:
                serial = f'127.0.0.1:{port}'
        except ValueError:
            pass
        # 夜神模拟器 127.0.0.1:62001
        # MuMu模拟器12127.0.0.1:16384
        if '模拟' in serial:
            res = re.search(r'(127\.\d+\.\d+\.\d+:\d+)', serial)
            if res:
                serial = res.group(1)
        # 12127.0.0.1:16384
        serial = serial.replace('12127.0.0.1', '127.0.0.1')
        # auto127.0.0.1:16384
        serial = serial.replace('auto127.0.0.1', '127.0.0.1').replace('autoemulator', 'emulator')
        return str(serial)

    def serial_check(self):
        """
        serial check
        """
        # fool-proof
        new = self.revise_serial(self.serial)
        if new != self.serial:
            logger.warning(f'Serial "{self.config.Emulator_Serial}" is revised to "{new}"')
            self.config.Emulator_Serial = new
            self.serial = new
        if self.is_bluestacks4_hyperv:
            self.serial = self.find_bluestacks4_hyperv(self.serial)
        if self.is_bluestacks5_hyperv:
            self.serial = self.find_bluestacks5_hyperv(self.serial)
        if "127.0.0.1:58526" in self.serial:
            logger.warning('Serial 127.0.0.1:58526 seems to be WSA, '
                           'please use "wsa-0" or others instead')
            raise RequestHumanTakeover
        if self.is_wsa:
            self.serial = '127.0.0.1:58526'
            if self.config.Emulator_ScreenshotMethod != 'uiautomator2' \
                    or self.config.Emulator_ControlMethod != 'uiautomator2':
                with self.config.multi_set():
                    self.config.Emulator_ScreenshotMethod = 'uiautomator2'
                    self.config.Emulator_ControlMethod = 'uiautomator2'
        if self.is_over_http:
            if self.config.Emulator_ScreenshotMethod not in ["ADB", "uiautomator2", "aScreenCap"] \
                    or self.config.Emulator_ControlMethod not in ["ADB", "uiautomator2", "minitouch"]:
                logger.warning(
                    f'When connecting to a device over http: {self.serial} '
                    f'ScreenshotMethod can only use ["ADB", "uiautomator2", "aScreenCap"], '
                    f'ControlMethod can only use ["ADB", "uiautomator2", "minitouch"]'
                )
                raise RequestHumanTakeover

    @cached_property
    def is_bluestacks4_hyperv(self):
        return "bluestacks4-hyperv" in self.serial

    @cached_property
    def is_bluestacks5_hyperv(self):
        return "bluestacks5-hyperv" in self.serial

    @cached_property
    def is_bluestacks_hyperv(self):
        return self.is_bluestacks4_hyperv or self.is_bluestacks5_hyperv

    @cached_property
    def is_wsa(self):
        return bool(re.match(r'^wsa', self.serial))

    @cached_property
    def port(self) -> int:
        port_serial, _ = get_serial_pair(self.serial)
        if port_serial is None:
            port_serial = self.serial
        try:
            return int(port_serial.split(':')[1])
        except (IndexError, ValueError):
            return 0

    @cached_property
    def is_mumu12_family(self):
        # 127.0.0.1:16XXX
        return 16384 <= self.port <= 17408

    @cached_property
    def is_mumu_family(self):
        # 127.0.0.1:7555
        # 127.0.0.1:16384 + 32*n
        return self.serial == '127.0.0.1:7555' or self.is_mumu12_family

    @cached_property
    def is_ldplayer_bluestacks_family(self):
        # Note that LDPlayer and BlueStacks have the same serial range
        return self.serial.startswith('emulator-') or 5555 <= self.port <= 5587

    @cached_property
    def is_nox_family(self):
        return 62001 <= self.port <= 63025

    @cached_property
    def is_vmos(self):
        return 5667 <= self.port <= 5699

    @cached_property
    def is_emulator(self):
        return self.serial.startswith('emulator-') or self.serial.startswith('127.0.0.1:')

    @cached_property
    def is_network_device(self):
        return bool(re.match(r'\d+\.\d+\.\d+\.\d+:\d+', self.serial))

    @cached_property
    def is_local_network_device(self):
        return bool(re.match(r'192\.168\.\d+\.\d+:\d+', self.serial))

    @cached_property
    def is_over_http(self):
        return bool(re.match(r"^https?://", self.serial))

    @cached_property
    def is_chinac_phone_cloud(self):
        # Phone cloud with public ADB connection
        # Serial like xxx.xxx.xxx.xxx:301
        return bool(re.search(r":30[0-9]$", self.serial))

    @staticmethod
    def find_bluestacks4_hyperv(serial):
        """
        Find dynamic serial of BlueStacks4 Hyper-V Beta.

        Args:
            serial (str): 'bluestacks4-hyperv', 'bluestacks4-hyperv-2' for multi instance, and so on.

        Returns:
            str: 127.0.0.1:{port}
        """
        from winreg import HKEY_LOCAL_MACHINE, OpenKey, QueryValueEx

        logger.info("Use BlueStacks4 Hyper-V Beta")
        logger.info("Reading Realtime adb port")

        if serial == "bluestacks4-hyperv":
            folder_name = "Android"
        else:
            folder_name = f"Android_{serial[19:]}"

        try:
            with OpenKey(HKEY_LOCAL_MACHINE,
                         rf"SOFTWARE\BlueStacks_bgp64_hyperv\Guests\{folder_name}\Config") as key:
                port = QueryValueEx(key, "BstAdbPort")[0]
        except FileNotFoundError:
            logger.error(
                rf'Unable to find registry HKEY_LOCAL_MACHINE\SOFTWARE\BlueStacks_bgp64_hyperv\Guests\{folder_name}\Config')
            logger.error('Please confirm that your are using BlueStack 4 hyper-v and not regular BlueStacks 4')
            logger.error(r'Please check if there is any other emulator instances under '
                         r'registry HKEY_LOCAL_MACHINE\SOFTWARE\BlueStacks_bgp64_hyperv\Guests')
            raise RequestHumanTakeover
        logger.info(f"New adb port: {port}")
        return f"127.0.0.1:{port}"

    @staticmethod
    def find_bluestacks5_hyperv(serial):
        """
        Find dynamic serial of BlueStacks5 Hyper-V.

        Args:
            serial (str): 'bluestacks5-hyperv', 'bluestacks5-hyperv-1' for multi instance, and so on.

        Returns:
            str: 127.0.0.1:{port}
        """
        from winreg import HKEY_LOCAL_MACHINE, OpenKey, QueryValueEx

        logger.info("Use BlueStacks5 Hyper-V")
        logger.info("Reading Realtime adb port")

        if serial == "bluestacks5-hyperv":
            parameter_name = r"bst\.instance\.(Nougat64|Pie64|Rvc64)\.status\.adb_port"
        else:
            parameter_name = rf"bst\.instance\.(Nougat64|Pie64|Rvc64)_{serial[19:]}\.status.adb_port"

        try:
            with OpenKey(HKEY_LOCAL_MACHINE, r"SOFTWARE\BlueStacks_nxt") as key:
                directory = QueryValueEx(key, 'UserDefinedDir')[0]
        except FileNotFoundError:
            try:
                with OpenKey(HKEY_LOCAL_MACHINE, r"SOFTWARE\BlueStacks_nxt_cn") as key:
                    directory = QueryValueEx(key, 'UserDefinedDir')[0]
            except FileNotFoundError:
                logger.error('Unable to find registry HKEY_LOCAL_MACHINE\SOFTWARE\BlueStacks_nxt '
                             'or HKEY_LOCAL_MACHINE\SOFTWARE\BlueStacks_nxt_cn')
                logger.error('Please confirm that you are using BlueStacks 5 hyper-v and not regular BlueStacks 5')
                raise RequestHumanTakeover
        logger.info(f"Configuration file directory: {directory}")

        with open(os.path.join(directory, 'bluestacks.conf'), encoding='utf-8') as f:
            content = f.read()
        port = re.search(rf'{parameter_name}="(\d+)"', content)
        if port is None:
            logger.warning(f"Did not match the result: {serial}.")
            raise RequestHumanTakeover
        port = port.group(2)
        logger.info(f"Match to dynamic port: {port}")
        return f"127.0.0.1:{port}"

    @cached_property
    def adb_binary(self):
        # Try adb in deploy.yaml
        from module.webui.setting import State
        file = State.deploy_config.AdbExecutable
        file = file.replace('\\', '/')
        if os.path.exists(file):
            return os.path.abspath(file)

        # Try existing adb.exe
        for file in self.adb_binary_list:
            if os.path.exists(file):
                return os.path.abspath(file)

        # Try adb in python environment
        import sys
        file = os.path.join(sys.executable, '../Lib/site-packages/adbutils/binaries/adb.exe')
        file = os.path.abspath(file).replace('\\', '/')
        if os.path.exists(file):
            return file

        # Use adb in system PATH
        file = 'adb'
        return file

    @cached_property
    def adb_client(self) -> AdbClient:
        host = '127.0.0.1'
        port = 5037

        # Trying to get adb port from env
        env = os.environ.get('ANDROID_ADB_SERVER_PORT', None)
        if env is not None:
            try:
                port = int(env)
            except ValueError:
                logger.warning(f'Invalid environ variable ANDROID_ADB_SERVER_PORT={port}, using default port')

        logger.attr('AdbClient', f'AdbClient({host}, {port})')
        return AdbClient(host, port)

    @cached_property
    def adb(self) -> AdbDevice:
        return AdbDevice(self.adb_client, self.serial)

    @cached_property
    def u2(self) -> u2.Device:
        if self.is_over_http:
            # Using uiautomator2_http
            device = u2.connect(self.serial)
        else:
            # Normal uiautomator2
            if self.serial.startswith('emulator-') or self.serial.startswith('127.0.0.1:'):
                device = u2.connect_usb(self.serial)
            else:
                device = u2.connect(self.serial)

        # Stay alive
        device.set_new_command_timeout(604800)

        logger.attr('u2.Device', f'Device(atx_agent_url={device._get_atx_agent_url()})')
        return device
