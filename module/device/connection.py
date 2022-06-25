import ipaddress
import logging
import platform
import re
import socket
import subprocess
import time
from functools import wraps

import uiautomator2 as u2
from adbutils import AdbClient, AdbDevice, AdbTimeout, ForwardItem, ReverseItem
from adbutils.errors import AdbError

from module.base.decorator import cached_property
from module.base.utils import ensure_time
from module.config.server import set_server
from module.device.connection_attr import ConnectionAttr
from module.device.method.utils import (RETRY_DELAY, RETRY_TRIES,
                                        handle_adb_error, PackageNotInstalled,
                                        recv_all, del_cached_property, possible_reasons,
                                        random_port, get_serial_pair)
from module.exception import RequestHumanTakeover
from module.logger import logger
from module.map.map_grids import SelectedGrids


def retry(func):
    @wraps(func)
    def retry_wrapper(self, *args, **kwargs):
        """
        Args:
            self (Adb):
        """
        init = None
        for _ in range(RETRY_TRIES):
            try:
                if callable(init):
                    self.sleep(RETRY_DELAY)
                    init()
                return func(self, *args, **kwargs)
            # Can't handle
            except RequestHumanTakeover:
                break
            # When adb server was killed
            except ConnectionResetError as e:
                logger.error(e)

                def init():
                    self.adb_reconnect()
            # AdbError
            except AdbError as e:
                if handle_adb_error(e):
                    def init():
                        self.adb_reconnect()
                else:
                    break
            # Package not installed
            except PackageNotInstalled as e:
                logger.error(e)

                def init():
                    self.detect_package()
            # Unknown, probably a trucked image
            except Exception as e:
                logger.exception(e)

                def init():
                    pass

        logger.critical(f'Retry {func.__name__}() failed')
        raise RequestHumanTakeover

    return retry_wrapper


class Connection(ConnectionAttr):
    def __init__(self, config):
        """
        Args:
            config (AzurLaneConfig, str): Name of the user config under ./config
        """
        super().__init__(config)
        self.detect_device()

        # Connect
        self.adb_connect(self.serial)
        logger.attr('AdbDevice', self.adb)

        # Package
        self.package = self.config.Emulator_PackageName
        if self.package == 'auto':
            self.detect_package()
        else:
            set_server(self.package)
        logger.attr('PackageName', self.package)
        logger.attr('Server', self.config.SERVER)

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
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            logger.warning(f'TimeoutExpired when calling {cmd}, stdout={stdout}, stderr={stderr}')
        return stdout

    def adb_shell(self, cmd, **kwargs):
        """
        Equivalent to `adb -s <serial> shell <*cmd>`

        Args:
            cmd (list, str):
            **kwargs:
                rstrip (bool): strip the last empty line (Default: True)
                stream (bool): return stream instead of string output (Default: False)

        Returns:
            str or socket if stream=True
        """
        if not isinstance(cmd, str):
            cmd = list(map(str, cmd))
        result = self.adb.shell(cmd, timeout=10, **kwargs)
        return result

    @cached_property
    def is_avd(self):
        if get_serial_pair(self.serial)[0] is None:
            return False
        if 'ranchu' in self.adb_shell(['getprop', 'ro.hardware']):
            return True
        if 'goldfish' in self.adb_shell(['getprop', 'ro.hardware.audio.primary']):
            return True
        return False

    @cached_property
    def _nc_server_host_port(self):
        """
        Returns:
            str, int, str, int:
                server_listen_host, server_listen_port, client_connect_host, client_connect_port
        """
        # For BlueStacks hyper-v, use ADB reverse
        if self.is_bluestacks_hyperv:
            host = '127.0.0.1'
            logger.info(f'Connecting to BlueStacks hyper-v, using host {host}')
            port = self.adb_reverse(f'tcp:{self.config.REVERSE_SERVER_PORT}')
            return host, port, host, self.config.REVERSE_SERVER_PORT
        # For emulators, listen on current host
        if self.is_emulator:
            host = socket.gethostbyname(socket.gethostname())
            if platform.system() == 'Linux' and host == '127.0.1.1':
                host = '127.0.0.1'
            logger.info(f'Connecting to local emulator, using host {host}')
            port = random_port(self.config.FORWARD_PORT_RANGE)

            # For AVD instance
            if self.is_avd:
                return host, port, "10.0.2.2", port

            return host, port, host, port
        # For local network devices, listen on the host under the same network as target device
        if self.is_network_device:
            hosts = socket.gethostbyname_ex(socket.gethostname())[2]
            logger.info(f'Current hosts: {hosts}')
            ip = ipaddress.ip_address(self.serial.split(':')[0])
            for host in hosts:
                if ip in ipaddress.ip_interface(f'{host}/24').network:
                    logger.info(f'Connecting to local network device, using host {host}')
                    port = random_port(self.config.FORWARD_PORT_RANGE)
                    return host, port, host, port
        # For other devices, create an ADB reverse and listen on 127.0.0.1
        host = '127.0.0.1'
        logger.info(f'Connecting to unknown device, using host {host}')
        port = self.adb_reverse(f'tcp:{self.config.REVERSE_SERVER_PORT}')
        return host, port, host, self.config.REVERSE_SERVER_PORT

    @cached_property
    def reverse_server(self):
        """
        Setup a server on Alas, access it from emulator.
        This will bypass adb shell and be faster.
        """
        del_cached_property(self, '_nc_server_host_port')
        host_port = self._nc_server_host_port
        logger.info(f'Reverse server listening on {host_port[0]}:{host_port[1]}, '
                    f'client can send data to {host_port[2]}:{host_port[3]}')
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(host_port[:2])
        server.listen(5)
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
        # Server start listening
        server = self.reverse_server
        server.settimeout(timeout)
        # Client send data, waiting for server accept
        # <command> | nc 127.0.0.1 {port}
        cmd += ['|', 'nc', *self._nc_server_host_port[2:]]
        stream = self.adb_shell(cmd, stream=True)
        try:
            # Server accept connection
            conn, conn_port = server.accept()
        except socket.timeout:
            output = recv_all(stream, chunk_size=chunk_size)
            logger.warning(str(output))
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
        if 'emulator' in serial or self.is_over_http:
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
                elif '(10061)' in msg:
                    # cannot connect to 127.0.0.1:55555:
                    # No connection could be made because the target machine actively refused it. (10061)
                    logger.error(msg)
                    possible_reasons('No such device exists, please set a correct serial')
                    raise RequestHumanTakeover
            logger.warning(f'Failed to connect {serial} after 3 trial, assume connected')
            self.detect_device()
            return False

    def adb_disconnect(self, serial):
        msg = self.adb_client.disconnect(serial)
        if msg:
            logger.info(msg)

        del_cached_property(self, 'hermit_session')
        del_cached_property(self, 'minitouch_builder')
        del_cached_property(self, 'reverse_server')

    def adb_restart(self):
        """
            Reboot adb client
        """
        logger.info('Restart adb')
        # Kill current client
        self.adb_client.server_kill()
        # Init adb client
        del_cached_property(self, 'adb_client')
        _ = self.adb_client

    def adb_reconnect(self):
        """
           Reboot adb client if no device found, otherwise try reconnecting device.
        """
        if self.config.Emulator_AdbRestart and len(self.list_device()) == 0:
            # Restart Adb
            self.adb_restart()
            # Connect to device
            self.adb_connect(self.serial)
            self.detect_device()
        else:
            self.adb_disconnect(self.serial)
            self.adb_connect(self.serial)
            self.detect_device()

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

    @retry
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
            r'.*DisplayViewport{.*valid=true, .*orientation=(?P<orientation>\d+), .*deviceWidth=(?P<width>\d+), deviceHeight=(?P<height>\d+).*'
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

    @retry
    def list_device(self):
        """
        Returns:
            SelectedGrids[AdbDeviceWithStatus]:
        """

        class AdbDeviceWithStatus(AdbDevice):
            def __init__(self, client: AdbClient, serial: str, status: str):
                self.status = status
                super().__init__(client, serial)

            def __str__(self):
                return f'AdbDevice({self.serial}, {self.status})'

            __repr__ = __str__

            def __bool__(self):
                return True

        devices = []
        with self.adb_client._connect() as c:
            c.send_command("host:devices")
            c.check_okay()
            output = c.read_string_block()
            for line in output.splitlines():
                parts = line.strip().split("\t")
                if len(parts) != 2:
                    continue
                device = AdbDeviceWithStatus(self.adb_client, parts[0], parts[1])
                devices.append(device)
        return SelectedGrids(devices)

    def detect_device(self):
        """
        Find available devices
        If serial=='auto' and only 1 device detected, use it
        """
        logger.hr('Detect device')
        logger.info('Here are the available devices, '
                    'copy to Alas.Emulator.Serial to use it or set Alas.Emulator.Serial="auto"')
        devices = self.list_device()

        # Show available devices
        available = devices.select(status='device')
        for device in available:
            logger.info(device.serial)
        if not len(available):
            logger.info('No available devices')

        # Show unavailable devices if having any
        unavailable = devices.delete(available)
        if len(unavailable):
            logger.info('Here are the devices detected but unavailable')
            for device in unavailable:
                logger.info(f'{device.serial} ({device.status})')

        # Auto device detection
        if self.config.Emulator_Serial == 'auto':
            if available.count == 0:
                logger.critical('No available device found, auto device detection cannot work, '
                                'please set an exact serial in Alas.Emulator.Serial instead of using "auto"')
                raise RequestHumanTakeover
            elif available.count == 1:
                logger.info(f'Auto device detection found only one device, using it')
                self.serial = devices[0].serial
                del_cached_property(self, 'adb')
            else:
                logger.critical('Multiple devices found, auto device detection cannot decide which to choose, '
                                'please copy one of the available devices listed above to Alas.Emulator.Serial')
                raise RequestHumanTakeover

        # Handle LDPlayer
        # LDPlayer serial jumps between `127.0.0.1:5555+{X}` and `emulator-5554+{X}`
        port_serial, emu_serial = get_serial_pair(self.serial)
        if port_serial and emu_serial:
            # Might be LDPlayer, check connected devices
            port_device = devices.select(serial=port_serial).first_or_none()
            emu_device = devices.select(serial=emu_serial).first_or_none()
            if port_device and emu_device:
                # Paired devices found, check status to get the correct one
                if port_device.status == 'device' and emu_device.status == 'offline':
                    self.serial = port_serial
                    logger.info(f'LDPlayer device pair found: {port_device}, {emu_device}. '
                                f'Using serial: {self.serial}')
                elif port_device.status == 'offline' and emu_device.status == 'device':
                    self.serial = emu_serial
                    logger.info(f'LDPlayer device pair found: {port_device}, {emu_device}. '
                                f'Using serial: {self.serial}')
            elif not devices.select(serial=self.serial):
                # Current serial not found
                if port_device and not emu_device:
                    logger.info(f'Current serial {self.serial} not found but paired device {port_serial} found. '
                                f'Using serial: {port_serial}')
                    self.serial = port_serial
                if not port_device and emu_device:
                    logger.info(f'Current serial {self.serial} not found but paired device {emu_serial} found. '
                                f'Using serial: {emu_serial}')
                    self.serial = emu_serial

    @retry
    def list_package(self):
        """
        Find all packages on device.
        Use dumpsys first for faster.
        """
        # 80ms
        logger.info('Get package list')
        output = self.adb_shell(r'dumpsys package | grep "Package \["')
        packages = re.findall(r'Package \[([^\s]+)\]', output)
        if len(packages):
            return packages

        # 200ms
        logger.info('Get package list')
        output = self.adb_shell(['pm', 'list', 'packages'])
        packages = re.findall(r'package:([^\s]+)', output)
        return packages

    def detect_package(self, keywords=('azurlane', 'blhx'), set_config=True):
        """
        Show all possible packages with the given keyword on this device.
        """
        logger.hr('Detect package')
        packages = self.list_package()
        packages = [p for p in packages if any([k in p.lower() for k in keywords])]

        # Show packages
        logger.info(f'Here are the available packages in device "{self.serial}", '
                    f'copy to Alas.Emulator.PackageName to use it')
        if len(packages):
            for package in packages:
                logger.info(package)
        else:
            logger.info(f'No available packages on device "{self.serial}"')

        # Auto package detection
        if len(packages) == 0:
            logger.critical(f'No {keywords[0]} package found, '
                            f'please confirm {keywords[0]} has been installed on device "{self.serial}"')
            raise RequestHumanTakeover
        if len(packages) == 1:
            logger.info('Auto package detection found only one package, using it')
            self.package = packages[0]
            # Set config
            if set_config:
                self.config.Emulator_PackageName = self.package
            # Set server
            logger.info('Server changed, release resources')
            set_server(self.package)
        else:
            logger.critical(
                f'Multiple {keywords[0]} packages found, auto package detection cannot decide which to choose, '
                'please copy one of the available devices listed above to Alas.Emulator.PackageName')
            raise RequestHumanTakeover
