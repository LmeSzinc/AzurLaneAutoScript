import logging
import os
import re
import socket
import subprocess
import time

import adbutils
import uiautomator2 as u2
from adbutils import AdbClient, AdbDevice, ForwardItem, ReverseItem, AdbTimeout

from deploy.utils import poor_yaml_read, DEPLOY_CONFIG
from module.base.decorator import cached_property
from module.base.utils import ensure_time
from module.config.config import AzurLaneConfig
from module.device.method.utils import recv_all, possible_reasons, random_port, del_cached_property
from module.exception import RequestHumanTakeover
from module.logger import logger


class Connection:
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
        logger.hr('Device')
        if isinstance(config, str):
            self.config = AzurLaneConfig(config, task=None)
        else:
            self.config = config

        self.serial = str(self.config.Emulator_Serial)
        if "bluestacks4-hyperv" in self.serial:
            self.serial = self.find_bluestacks4_hyperv(self.serial)
        if "bluestacks5-hyperv" in self.serial:
            self.serial = self.find_bluestacks5_hyperv(self.serial)
        if "127.0.0.1:58526" in self.serial:
            logger.warning('Serial 127.0.0.1:58526 seems to be WSA, '
                           'please use "wsa-0" or others instead')
            raise RequestHumanTakeover
        if "wsa" in self.serial:
            self.serial = '127.0.0.1:58526'

        logger.attr('Adb_binary', self.adb_binary)

        # Monkey patch to custom adb
        adbutils.adb_path = lambda: self.adb_binary
        # Remove global proxies, or uiautomator2 will go through it
        for k in list(os.environ.keys()):
            if k.lower().endswith('_proxy'):
                del os.environ[k]

        self.adb_client = AdbClient('127.0.0.1', 5037)
        self.adb_connect(self.serial)

        self.adb = AdbDevice(self.adb_client, self.serial)
        logger.attr('Adb_device', self.adb)

    @staticmethod
    def find_bluestacks4_hyperv(serial):
        """
        Find dynamic serial of Bluestacks4 Hyper-v Beta.

        Args:
            serial (str): 'bluestacks4-hyperv', 'bluestacks4-hyperv-2' for multi instance, and so on.

        Returns:
            str: 127.0.0.1:{port}
        """
        from winreg import ConnectRegistry, OpenKey, QueryInfoKey, EnumValue, CloseKey, HKEY_LOCAL_MACHINE

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

    @staticmethod
    def find_bluestacks5_hyperv(serial):
        """
        Find dynamic serial of Bluestacks5 Hyper-v.

        Args:
            serial (str): 'bluestacks5-hyperv', 'bluestacks5-hyperv-1' for multi instance, and so on.

        Returns:
            str: 127.0.0.1:{port}
        """
        from winreg import ConnectRegistry, OpenKey, QueryInfoKey, EnumValue, CloseKey, HKEY_LOCAL_MACHINE

        logger.info("Use Bluestacks5 Hyper-v")
        logger.info("Reading Realtime adb port")

        if serial == "bluestacks5-hyperv":
            parameter_name = "bst.instance.Nougat64.status.adb_port"
        else:
            parameter_name = f"bst.instance.Nougat64_{serial[19:]}.status.adb_port"

        reg_root = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
        sub_dir = f"SOFTWARE\\BlueStacks_nxt"
        bs_keys = OpenKey(reg_root, sub_dir)
        bs_keys_count = QueryInfoKey(bs_keys)[1]
        for i in range(bs_keys_count):
            key_name, key_value, key_type = EnumValue(bs_keys, i)
            if key_name == "UserDefinedDir":
                logger.info(f"Configuration file directory: {key_value}")
                with open(f"{key_value}\\bluestacks.conf", 'r', encoding='utf-8') as f:
                    content = f.read()
                    port = re.findall(rf'{parameter_name}="(.*?)"\n', content, re.S)
                    if len(port) > 0:
                        logger.info(f"Match to dynamic port: {port[0]}")
                        serial = f"127.0.0.1:{port[0]}"
                    else:
                        logger.warning(f"Did not match the result: {serial}.")
                break

        CloseKey(bs_keys)
        CloseKey(reg_root)
        return serial

    @cached_property
    def adb_binary(self):
        # Try adb in deploy.yaml
        config = poor_yaml_read(DEPLOY_CONFIG)
        if 'AdbExecutable' in config:
            file = config['AdbExecutable'].replace('\\', '/')
            if os.path.exists(file):
                return os.path.abspath(file)

        # Try existing adb.exe
        for file in self.adb_binary_list:
            if os.path.exists(file):
                return os.path.abspath(file)

        # Use adb.exe in system PATH
        file = 'adb.exe'
        return file

    def adb_command(self, cmd, timeout=10):
        """
        Execute ADB commands in a subprocess,
        usually to be used when pulling or pushing large files.

        Args:
            cmd (list):
            timeout (int):

        Returns:
            str:
        """
        cmd = list(map(str, cmd))
        cmd = [self.adb_binary, '-s', self.serial] + cmd

        # Use shell=True to disable console window when using GUI.
        # Although, there's still a window when you stop running in GUI, which cause by gooey.
        # To disable it, edit gooey/gui/util/taskkill.py

        # No gooey anymore, just shell=False
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=False)
        return process.communicate(timeout=timeout)[0]

    def adb_shell(self, cmd, **kwargs):
        """
        Equivalent to `adb -s <serial> shell <*cmd>`

        Args:
            cmd (list):
            **kwargs:
                rstrip (bool): strip the last empty line (Default: True)
                stream (bool): return stream instead of string output (Default: False)

        Returns:
            str or socket if stream=True
        """
        cmd = list(map(str, cmd))
        result = self.adb.shell(cmd, timeout=10, **kwargs)
        return result

    @cached_property
    def reverse_server(self):
        """
        Setup a server on Alas, access it from emulator.
        This will bypass adb shell and be faster.
        """
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_port = self.adb_reverse(f'tcp:{self.config.REVERSE_SERVER_PORT}')
        server.bind(('127.0.0.1', self._server_port))
        server.listen(5)
        logger.info(f'Reverse server listening on {self._server_port}')
        return server

    def adb_shell_nc(self, cmd, timeout=5, chunk_size=262144):
        """
        Args:
            cmd (list):
            timeout (int):
            chunk_size (int): Default to 262144

        Returns:
            bytes:
        """
        # <command> | nc 127.0.0.1 {port}
        cmd += ['|', 'nc', '127.0.0.1', self.config.REVERSE_SERVER_PORT]

        # Server start listening
        server = self.reverse_server
        server.settimeout(timeout)
        # Client send data, waiting for server accept
        _ = self.adb_shell(cmd, stream=True)
        try:
            # Server accept connection
            conn, conn_port = server.accept()
        except socket.timeout:
            raise AdbTimeout('reverse server accept timeout')

        # Server receive data
        data = recv_all(conn, chunk_size=chunk_size)

        # Server close connection
        conn.close()
        return data

    def adb_exec_out(self, cmd, serial=None):
        cmd.insert(0, 'exec-out')
        return self.adb_command(cmd, serial)

    def adb_forward(self, remote):
        """
        Do `adb forward <local> <remote>`.
        choose a random port in FORWARD_PORT_RANGE or reuse an existing forward,
        and also remove redundant forwards.

        Args:
            remote (str):
                tcp:<port>
                localabstract:<unix domain socket name>
                localreserved:<unix domain socket name>
                localfilesystem:<unix domain socket name>
                dev:<character device name>
                jdwp:<process pid> (remote only)

        Returns:
            int: Port
        """
        port = 0
        for forward in self.adb.forward_list():
            if forward.serial == self.serial and forward.remote == remote and forward.local.startswith('tcp:'):
                if not port:
                    logger.info(f'Reuse forward: {forward}')
                    port = int(forward.local[4:])
                else:
                    logger.info(f'Remove redundant forward: {forward}')
                    self.adb_forward_remove(forward.local)

        if port:
            return port
        else:
            # Create new forward
            port = random_port(self.config.FORWARD_PORT_RANGE)
            forward = ForwardItem(self.serial, f'tcp:{port}', remote)
            logger.info(f'Create forward: {forward}')
            self.adb.forward(forward.local, forward.remote)
            return port

    def adb_reverse(self, remote):
        port = 0
        for reverse in self.adb.reverse_list():
            if reverse.remote == remote and reverse.local.startswith('tcp:'):
                if not port:
                    logger.info(f'Reuse reverse: {reverse}')
                    port = int(reverse.local[4:])
                else:
                    logger.info(f'Remove redundant forward: {reverse}')
                    self.adb_forward_remove(reverse.local)

        if port:
            return port
        else:
            # Create new reverse
            port = random_port(self.config.FORWARD_PORT_RANGE)
            reverse = ReverseItem(f'tcp:{port}', remote)
            logger.info(f'Create reverse: {reverse}')
            self.adb.reverse(reverse.local, reverse.remote)
            return port

    def adb_forward_remove(self, local):
        """
        Equivalent to `adb -s <serial> forward --remove <local>`
        More about the commands send to ADB server, see:
        https://cs.android.com/android/platform/superproject/+/master:packages/modules/adb/SERVICES.TXT

        Args:
            local (str): Such as 'tcp:2437'
        """
        with self.adb_client._connect() as c:
            list_cmd = f"host-serial:{self.serial}:killforward:{local}"
            c.send_command(list_cmd)
            c.check_okay()

    def adb_reverse_remove(self, local):
        """
        Equivalent to `adb -s <serial> reverse --remove <local>`

        Args:
            local (str): Such as 'tcp:2437'
        """
        with self.adb_client._connect() as c:
            c.send_command(f"host:transport:{self.serial}")
            c.check_okay()
            list_cmd = f"reverse:killforward:{local}"
            c.send_command(list_cmd)
            c.check_okay()

    def adb_push(self, local, remote):
        """
        Args:
            local (str):
            remote (str):

        Returns:
            str:
        """
        cmd = ['push', local, remote]
        return self.adb_command(cmd)

    def adb_connect(self, serial):
        """
        Connect to a serial, try 3 times at max.
        If there's an old ADB server running while Alas is using a newer one, which happens on Chinese emulators,
        the first connection is used to kill the other one, and the second is the real connect.

        Args:
            serial (str):

        Returns:
            bool: If success
        """
        if 'emulator' in serial:
            return True
        else:
            for _ in range(3):
                msg = self.adb_client.connect(serial)
                logger.info(msg)
                if 'connected' in msg:
                    # Connected to 127.0.0.1:59865
                    # Already connected to 127.0.0.1:59865
                    return True
                elif 'bad port' in msg:
                    # bad port number '598265' in '127.0.0.1:598265'
                    logger.error(msg)
                    possible_reasons('Serial incorrect, might be a typo')
                    raise RequestHumanTakeover
            logger.warning(f'Failed to connect {serial} after 3 trial, assume connected')
            self.show_devices()
            return False

    def adb_disconnect(self, serial):
        msg = self.adb_client.disconnect(serial)
        if msg:
            logger.info(msg)

        del_cached_property(self, 'hermit_session')
        del_cached_property(self, 'minitouch_builder')
        del_cached_property(self, 'reverse_server')

    def install_uiautomator2(self):
        """
        Init uiautomator2 and remove minicap.
        """
        logger.info('Install uiautomator2')
        init = u2.init.Initer(self.adb, loglevel=logging.DEBUG)
        init.set_atx_agent_addr('127.0.0.1:7912')
        init.install()
        self.uninstall_minicap()

    def uninstall_minicap(self):
        """ minicap can't work or will send compressed images on some emulators. """
        logger.info('Removing minicap')
        self.adb_shell(["rm", "/data/local/tmp/minicap"])
        self.adb_shell(["rm", "/data/local/tmp/minicap.so"])

    def restart_atx(self):
        """
        Minitouch supports only one connection at a time.
        Restart ATX to kick the existing one.
        """
        logger.info('Restart ATX')
        atx_agent_path = '/data/local/tmp/atx-agent'
        self.adb_shell([atx_agent_path, 'server', '--stop'])
        self.adb_shell([atx_agent_path, 'server', '--nouia', '-d', '--addr', '127.0.0.1:7912'])

    @staticmethod
    def sleep(second):
        """
        Args:
            second(int, float, tuple):
        """
        time.sleep(ensure_time(second))

    _orientation_description = {
        0: 'Normal',
        1: 'HOME key on the right',
        2: 'HOME key on the top',
        3: 'HOME key on the left',
    }
    orientation = 0

    def get_orientation(self):
        """
        Rotation of the phone

        Returns:
            int:
                0: 'Normal'
                1: 'HOME key on the right'
                2: 'HOME key on the top'
                3: 'HOME key on the left'
        """
        _DISPLAY_RE = re.compile(
            r'.*DisplayViewport{valid=true, .*orientation=(?P<orientation>\d+), .*deviceWidth=(?P<width>\d+), deviceHeight=(?P<height>\d+).*'
        )
        output = self.adb_shell(['dumpsys', 'display'])

        res = _DISPLAY_RE.search(output, 0)

        if res:
            o = int(res.group('orientation'))
            if o in Connection._orientation_description:
                pass
            else:
                o = 0
                logger.warning(f'Invalid device orientation: {o}, assume it is normal')
        else:
            o = 0
            logger.warning('Unable to get device orientation, assume it is normal')

        self.orientation = o
        logger.attr('Device Orientation', f'{o} ({Connection._orientation_description.get(o, "Unknown")})')
        return o

    def show_devices(self):
        """
        Show all available devices on current computer.
        """
        logger.hr('Show devices')
        logger.info('Here are the available devices, '
                    'copy to Alas.Emulator.Serial to use it')
        devices = list(self.adb_client.iter_device())
        if devices:
            for device in devices:
                logger.info(device.serial)
        else:
            logger.info('No available devices')

    def show_packages(self, keyword='azurlane'):
        """
        Show all possible packages with the given keyword on this device.
        """
        logger.hr('Show packages')
        logger.info('Fetching package list')
        output = self.adb_shell(['pm', 'list', 'packages'])
        packages = re.findall(r'package:([^\s]+)', output)
        logger.info(f'Here are the available packages in device {self.serial}, '
                    f'copy to Alas.Emulator.PackageName to use it')

        if packages:
            for package in packages:
                if keyword in package.lower():
                    logger.info(package)
        else:
            logger.info(f'No available package with keyword: {keyword}')
