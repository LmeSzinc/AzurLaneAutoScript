import ipaddress
import logging
import re
import socket
import subprocess
import time
from functools import wraps

import uiautomator2 as u2
from adbutils import AdbClient, AdbDevice, AdbTimeout, ForwardItem, ReverseItem
from adbutils.errors import AdbError

from module.base.decorator import Config, cached_property, del_cached_property, run_once
from module.base.utils import ensure_time
from module.config.server import VALID_CHANNEL_PACKAGE, VALID_PACKAGE, set_server
from module.device.connection_attr import ConnectionAttr
from module.device.env import IS_LINUX, IS_MACINTOSH, IS_WINDOWS
from module.device.method.utils import (PackageNotInstalled, RETRY_TRIES, get_serial_pair, handle_adb_error,
                                        handle_unknown_host_service, possible_reasons, random_port, recv_all,
                                        remove_shell_warning, retry_sleep)
from module.exception import EmulatorNotRunningError, RequestHumanTakeover
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
                    retry_sleep(_)
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
                elif handle_unknown_host_service(e):
                    def init():
                        self.adb_start_server()
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


class AdbDeviceWithStatus(AdbDevice):
    def __init__(self, client: AdbClient, serial: str, status: str):
        self.status = status
        super().__init__(client, serial)

    def __str__(self):
        return f'AdbDevice({self.serial}, {self.status})'

    __repr__ = __str__

    def __bool__(self):
        return True

    @cached_property
    def port(self) -> int:
        try:
            return int(self.serial.split(':')[1])
        except (IndexError, ValueError):
            return 0

    @cached_property
    def may_mumu12_family(self):
        # 127.0.0.1:16XXX
        return 16384 <= self.port <= 17408


class Connection(ConnectionAttr):
    def __init__(self, config):
        """
        Args:
            config (AzurLaneConfig, str): Name of the user config under ./config
        """
        super().__init__(config)
        if not self.is_over_http:
            self.detect_device()

        # Connect
        self.adb_connect()
        logger.attr('AdbDevice', self.adb)

        # Package
        self.package = self.config.Emulator_PackageName
        if self.package == 'auto':
            self.detect_package()
        else:
            set_server(self.package)
        logger.attr('PackageName', self.package)
        logger.attr('Server', self.config.SERVER)

        self.check_mumu_app_keep_alive()

    @Config.when(DEVICE_OVER_HTTP=False)
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
        return self.subprocess_run(cmd, timeout=timeout)

    def subprocess_run(self, cmd, timeout=10):
        """
        Args:
            cmd (list):
            timeout (int):

        Returns:
            str:
        """
        logger.info(f'Execute: {cmd}')
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

    @Config.when(DEVICE_OVER_HTTP=True)
    def adb_command(self, cmd, timeout=10):
        logger.critical(
            f'Trying to execute {cmd}, '
            f'but adb_command() is not available when connecting over http: {self.serial}, '
        )
        raise RequestHumanTakeover

    def adb_start_server(self):
        """
        Use `adb devices` as `adb start-server`, result is actually useless
        Start ADB using subprocess instead of connecting via socket to kill the other ADBs
        """
        stdout = self.subprocess_run([self.adb_binary, 'devices'])
        logger.info(stdout)
        return stdout

    @Config.when(DEVICE_OVER_HTTP=False)
    def adb_shell(self, cmd, stream=False, recvall=True, timeout=10, rstrip=True):
        """
        Equivalent to `adb -s <serial> shell <*cmd>`

        Args:
            cmd (list, str):
            stream (bool): Return stream instead of string output (Default: False)
            recvall (bool): Receive all data when stream=True (Default: True)
            timeout (int): (Default: 10)
            rstrip (bool): Strip the last empty line (Default: True)

        Returns:
            str if stream=False
            bytes if stream=True and recvall=True
            socket if stream=True and recvall=False
        """
        if not isinstance(cmd, str):
            cmd = list(map(str, cmd))

        if stream:
            result = self.adb.shell(cmd, stream=stream, timeout=timeout, rstrip=rstrip)
            if recvall:
                # bytes
                return recv_all(result)
            else:
                # socket
                return result
        else:
            result = self.adb.shell(cmd, stream=stream, timeout=timeout, rstrip=rstrip)
            result = remove_shell_warning(result)
            # str
            return result

    @Config.when(DEVICE_OVER_HTTP=True)
    def adb_shell(self, cmd, stream=False, recvall=True, timeout=10, rstrip=True):
        """
        Equivalent to http://127.0.0.1:7912/shell?command={command}

        Args:
            cmd (list, str):
            stream (bool): Return stream instead of string output (Default: False)
            recvall (bool): Receive all data when stream=True (Default: True)
            timeout (int): (Default: 10)
            rstrip (bool): Strip the last empty line (Default: True)

        Returns:
            str if stream=False
            bytes if stream=True
        """
        if not isinstance(cmd, str):
            cmd = list(map(str, cmd))

        if stream:
            result = self.u2.shell(cmd, stream=stream, timeout=timeout)
            # Already received all, so `recvall` is ignored
            result = remove_shell_warning(result.content)
            # bytes
            return result
        else:
            result = self.u2.shell(cmd, stream=stream, timeout=timeout).output
            if rstrip:
                result = result.rstrip()
            result = remove_shell_warning(result)
            # str
            return result

    def adb_getprop(self, name):
        """
        Get system property in Android, same as `getprop <name>`

        Args:
            name (str): Property name

        Returns:
            str:
        """
        return self.adb_shell(['getprop', name]).strip()

    @cached_property
    @retry
    def cpu_abi(self) -> str:
        """
        Returns:
            str: arm64-v8a, armeabi-v7a, x86, x86_64
        """
        abi = self.adb_getprop('ro.product.cpu.abi')
        if not len(abi):
            logger.error(f'CPU ABI invalid: "{abi}"')
        return abi

    @cached_property
    @retry
    def sdk_ver(self) -> int:
        """
        Android SDK/API levels, see https://apilevels.com/
        """
        sdk = self.adb_getprop('ro.build.version.sdk')
        try:
            return int(sdk)
        except ValueError:
            logger.error(f'SDK version invalid: {sdk}')

        return 0

    @cached_property
    @retry
    def is_avd(self):
        if get_serial_pair(self.serial)[0] is None:
            return False
        if 'ranchu' in self.adb_getprop('ro.hardware'):
            return True
        if 'goldfish' in self.adb_getprop('ro.hardware.audio.primary'):
            return True
        return False

    @cached_property
    @retry
    def is_waydroid(self):
        res = self.adb_getprop('ro.product.brand')
        logger.attr('ro.product.brand', res)
        return 'waydroid' in res.lower()

    @cached_property
    @retry
    def nemud_app_keep_alive(self) -> str:
        res = self.adb_getprop('nemud.app_keep_alive')
        logger.attr('nemud.app_keep_alive', res)
        return res

    @cached_property
    @retry
    def nemud_player_version(self) -> str:
        # [nemud.player_product_version]: [3.8.27.2950]
        res = self.adb_getprop('nemud.player_version')
        logger.attr('nemud.player_version', res)
        return res

    @cached_property
    @retry
    def nemud_player_engine(self) -> str:
        # NEMUX or MACPRO
        res = self.adb_getprop('nemud.player_engine')
        logger.attr('nemud.player_engine', res)
        return res

    def check_mumu_app_keep_alive(self):
        if not self.is_mumu_family:
            return False

        res = self.nemud_app_keep_alive
        if res == '':
            # Empty property, probably MuMu6 or MuMu12 version < 3.5.6
            return True
        elif res == 'false':
            # Disabled
            return True
        elif res == 'true':
            # https://mumu.163.com/help/20230802/35047_1102450.html
            logger.critical('请在MuMu模拟器设置内关闭 "后台挂机时保活运行"')
            raise RequestHumanTakeover
        else:
            logger.warning(f'Invalid nemud.app_keep_alive value: {res}')
            return False

    @cached_property
    def is_mumu_over_version_356(self) -> bool:
        """
        Returns:
            bool: If MuMu12 version >= 3.5.6,
                which has nemud.app_keep_alive and always be a vertical device
                MuMu PRO on mac has the same feature
        """
        if not self.is_mumu_family:
            return False
        # >= 4.0 has no info in getprop
        if self.nemud_player_version == '':
            return True
        if self.nemud_app_keep_alive != '':
            return True
        if IS_MACINTOSH:
            if 'MACPRO' in self.nemud_player_engine:
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
        if self.is_emulator or self.is_over_http:
            try:
                host = socket.gethostbyname(socket.gethostname())
            except socket.gaierror as e:
                logger.error(e)
                logger.error(f'Unknown host name: {socket.gethostname()}')
                host = '127.0.0.1'
            if IS_LINUX and host == '127.0.1.1':
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
        server.settimeout(5)
        server.listen(5)
        return server

    @cached_property
    def nc_command(self):
        """
        Returns:
            list[str]: ['nc'] or ['busybox', 'nc']
        """
        if self.is_emulator:
            sdk = self.sdk_ver
            logger.info(f'sdk_ver: {sdk}')
            if sdk >= 28:
                # LD Player 9 does not have `nc`, try `busybox nc`
                # BlueStacks Pie (Android 9) has `nc` but cannot send data, try `busybox nc` first
                trial = [
                    ['busybox', 'nc'],
                    ['nc'],
                ]
            else:
                trial = [
                    ['nc'],
                    ['busybox', 'nc'],
                ]
        else:
            trial = [
                ['nc'],
                ['busybox', 'nc'],
            ]
        for command in trial:
            # About 3ms
            # Result should be command help if success
            # nc: bad argument count (see "nc --help")
            result = self.adb_shell(command)
            # `/system/bin/sh: nc: not found`
            if 'not found' in result:
                continue
            # `/system/bin/sh: busybox: inaccessible or not found\n`
            if 'inaccessible' in result:
                continue
            logger.attr('nc command', command)
            return command

        logger.error('No `netcat` command available, please use screenshot methods without `_nc` suffix')
        raise RequestHumanTakeover

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
        cmd += ["|", *self.nc_command, *self._nc_server_host_port[2:]]
        stream = self.adb_shell(cmd, stream=True, recvall=False)
        try:
            # Server accept connection
            conn, conn_port = server.accept()
        except socket.timeout:
            output = recv_all(stream, chunk_size=chunk_size)
            logger.warning(str(output))
            raise AdbTimeout('reverse server accept timeout')

        # Server receive data
        data = recv_all(conn, chunk_size=chunk_size, recv_interval=0.001)

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
        No error raised when removing a non-existent forward

        More about the commands send to ADB server, see:
        https://cs.android.com/android/platform/superproject/+/master:packages/modules/adb/SERVICES.TXT

        Args:
            local (str): Such as 'tcp:2437'
        """
        try:
            with self.adb_client._connect() as c:
                list_cmd = f"host-serial:{self.serial}:killforward:{local}"
                c.send_command(list_cmd)
                c.check_okay()
        except AdbError as e:
            # No error raised when removing a non-existed forward
            # adbutils.errors.AdbError: listener 'tcp:8888' not found
            msg = str(e)
            if re.search(r'listener .*? not found', msg):
                logger.warning(f'{type(e).__name__}: {msg}')
            else:
                raise

    def adb_reverse_remove(self, local):
        """
        Equivalent to `adb -s <serial> reverse --remove <local>`
        No error raised when removing a non-existent reverse

        Args:
            local (str): Such as 'tcp:2437'
        """
        try:
            with self.adb_client._connect() as c:
                c.send_command(f"host:transport:{self.serial}")
                c.check_okay()
                list_cmd = f"reverse:killforward:{local}"
                c.send_command(list_cmd)
                c.check_okay()
        except AdbError as e:
            # No error raised when removing a non-existed forward
            # adbutils.errors.AdbError: listener 'tcp:8888' not found
            msg = str(e)
            if re.search(r'listener .*? not found', msg):
                logger.warning(f'{type(e).__name__}: {msg}')
            else:
                raise

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

    @Config.when(DEVICE_OVER_HTTP=False)
    def adb_connect(self):
        """
        Connect to a serial, try 3 times at max.
        If there's an old ADB server running while Alas is using a newer one, which happens on Chinese emulators,
        the first connection is used to kill the other one, and the second is the real connect.

        Args:
            serial (str):

        Returns:
            bool: If success
        """
        # Disconnect offline device before connecting
        for device in self.list_device():
            if device.status == 'offline':
                logger.warning(f'Device {device.serial} is offline, disconnect it before connecting')
                msg = self.adb_client.disconnect(device.serial)
                if msg:
                    logger.info(msg)
            elif device.status == 'unauthorized':
                logger.error(f'Device {device.serial} is unauthorized, please accept ADB debugging on your device')
            elif device.status == 'device':
                pass
            else:
                logger.warning(f'Device {device.serial} is is having a unknown status: {device.status}')

        # Skip for emulator-5554
        if 'emulator-' in self.serial:
            logger.info(f'"{self.serial}" is a `emulator-*` serial, skip adb connect')
            return True
        if re.match(r'^[a-zA-Z0-9]+$', self.serial):
            logger.info(f'"{self.serial}" seems to be a Android serial, skip adb connect')
            return True

        # Try to connect
        for _ in range(3):
            msg = self.adb_client.connect(self.serial)
            logger.info(msg)
            # Connected to 127.0.0.1:59865
            # Already connected to 127.0.0.1:59865
            if 'connected' in msg:
                return True
            # bad port number '598265' in '127.0.0.1:598265'
            elif 'bad port' in msg:
                possible_reasons('Serial incorrect, might be a typo')
                raise RequestHumanTakeover
            # cannot connect to 127.0.0.1:55555:
            # No connection could be made because the target machine actively refused it. (10061)
            elif '(10061)' in msg:
                # MuMu12 may switch serial if port is occupied
                # Brute force connect nearby ports to handle serial switches
                if self.is_mumu12_family:
                    before = self.serial
                    serial_list = [self.serial.replace(str(self.port), str(self.port + offset))
                                   for offset in [1, -1, 2, -2]]
                    self.adb_brute_force_connect(serial_list)
                    self.detect_device()
                    if self.serial != before:
                        return True
                # No such device
                logger.warning('No such device exists, please restart the emulator or set a correct serial')
                raise EmulatorNotRunningError

        # Failed to connect
        logger.warning(f'Failed to connect {self.serial} after 3 trial, assume connected')
        self.detect_device()
        return False

    def adb_brute_force_connect(self, serial_list):
        """
        Args:
            serial_list (list[str]):
        """
        import asyncio
        ev = asyncio.new_event_loop()

        def _connect(serial):
            msg = self.adb_client.connect(serial)
            logger.info(msg)
            return msg

        async def connect():
            tasks = [ev.run_in_executor(None, _connect, serial) for serial in serial_list]
            await asyncio.gather(*tasks)

        ev.run_until_complete(connect())

    @Config.when(DEVICE_OVER_HTTP=True)
    def adb_connect(self):
        # No adb connect if over http
        return True

    def release_resource(self):
        del_cached_property(self, 'hermit_session')
        del_cached_property(self, 'droidcast_session')
        del_cached_property(self, '_minitouch_builder')
        del_cached_property(self, '_maatouch_builder')
        del_cached_property(self, 'reverse_server')

    def adb_disconnect(self):
        msg = self.adb_client.disconnect(self.serial)
        if msg:
            logger.info(msg)
        self.release_resource()

    def adb_restart(self):
        """
            Reboot adb client
        """
        logger.info('Restart adb')
        # Kill current client
        self.adb_client.server_kill()
        # Init adb client
        del_cached_property(self, 'adb_client')
        self.release_resource()
        _ = self.adb_client

    @Config.when(DEVICE_OVER_HTTP=False)
    def adb_reconnect(self):
        """
           Reboot adb client if no device found, otherwise try reconnecting device.
        """
        if self.config.Emulator_AdbRestart and len(self.list_device()) == 0:
            # Restart Adb
            self.adb_restart()
            # Connect to device
            self.adb_connect()
            self.detect_device()
        else:
            self.adb_disconnect()
            self.adb_connect()
            self.detect_device()

    @Config.when(DEVICE_OVER_HTTP=True)
    def adb_reconnect(self):
        logger.warning(
            f'When connecting a device over http: {self.serial} '
            f'adb_reconnect() is skipped, you may need to restart ATX manually'
        )

    def install_uiautomator2(self):
        """
        Init uiautomator2 and remove minicap.
        """
        logger.info('Install uiautomator2')
        init = u2.init.Initer(self.adb, loglevel=logging.DEBUG)
        # MuMu X has no ro.product.cpu.abi, pick abi from ro.product.cpu.abilist
        if init.abi not in ['x86_64', 'x86', 'arm64-v8a', 'armeabi-v7a', 'armeabi']:
            init.abi = init.abis[0]
        init.set_atx_agent_addr('127.0.0.1:7912')
        try:
            init.install()
        except ConnectionError:
            u2.init.GITHUB_BASEURL = 'http://tool.appetizer.io/openatx'
            init.install()
        self.uninstall_minicap()

    def uninstall_minicap(self):
        """ minicap can't work or will send compressed images on some emulators. """
        logger.info('Removing minicap')
        self.adb_shell(["rm", "/data/local/tmp/minicap"])
        self.adb_shell(["rm", "/data/local/tmp/minicap.so"])

    @Config.when(DEVICE_OVER_HTTP=False)
    def restart_atx(self):
        """
        Minitouch supports only one connection at a time.
        Restart ATX to kick the existing one.
        """
        logger.info('Restart ATX')
        atx_agent_path = '/data/local/tmp/atx-agent'
        self.adb_shell([atx_agent_path, 'server', '--stop'])
        self.adb_shell([atx_agent_path, 'server', '--nouia', '-d', '--addr', '127.0.0.1:7912'])

    @Config.when(DEVICE_OVER_HTTP=True)
    def restart_atx(self):
        logger.warning(
            f'When connecting a device over http: {self.serial} '
            f'restart_atx() is skipped, you may need to restart ATX manually'
        )

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
        devices = []
        try:
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
        except ConnectionResetError as e:
            # Happens only on CN users.
            # ConnectionResetError: [WinError 10054] 远程主机强迫关闭了一个现有的连接。
            logger.error(e)
            if '强迫关闭' in str(e):
                logger.critical('无法连接至ADB服务，请关闭UU加速器、原神私服、以及一些劣质代理软件。'
                                '它们会劫持电脑上所有的网络连接，包括Alas与模拟器之间的本地连接。')
        return SelectedGrids(devices)

    def detect_device(self):
        """
        Find available devices
        If serial=='auto' and only 1 device detected, use it
        """
        logger.hr('Detect device')
        available = SelectedGrids([])
        devices = SelectedGrids([])

        @run_once
        def brute_force_connect():
            logger.info('Brute force connect')
            from deploy.Windows.emulator import EmulatorManager
            manager = EmulatorManager()
            manager.brute_force_connect()

        for _ in range(2):
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

            # brute_force_connect
            if self.config.Emulator_Serial == 'auto' and available.count == 0:
                logger.warning(f'No available device found')
                if IS_WINDOWS:
                    brute_force_connect()
                    continue
                else:
                    break
            else:
                break

        # Auto device detection
        if self.config.Emulator_Serial == 'auto':
            if available.count == 0:
                logger.critical('No available device found, auto device detection cannot work, '
                                'please set an exact serial in Alas.Emulator.Serial instead of using "auto"')
                raise RequestHumanTakeover
            elif available.count == 1:
                logger.info(f'Auto device detection found only one device, using it')
                self.config.Emulator_Serial = self.serial = available[0].serial
                del_cached_property(self, 'adb')
            elif available.count == 2 \
                    and available.select(serial='127.0.0.1:7555') \
                    and available.select(may_mumu12_family=True):
                logger.info(f'Auto device detection found MuMu12 device, using it')
                # For MuMu12 serials like 127.0.0.1:7555 and 127.0.0.1:16384
                # ignore 7555 use 16384
                remain = available.select(may_mumu12_family=True).first_or_none()
                self.config.Emulator_Serial = self.serial = remain.serial
                del_cached_property(self, 'adb')
            else:
                logger.critical('Multiple devices found, auto device detection cannot decide which to choose, '
                                'please copy one of the available devices listed above to Alas.Emulator.Serial')
                raise RequestHumanTakeover

        # Handle LDPlayer
        # LDPlayer serial jumps between `127.0.0.1:5555+{X}` and `emulator-5554+{X}`
        # No config write since it's dynamic
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

        # Redirect MuMu12 from 127.0.0.1:7555 to 127.0.0.1:16xxx
        if (
                (IS_WINDOWS and self.serial == '127.0.0.1:7555')
                or (IS_MACINTOSH and self.serial == '127.0.0.1:5555')
        ):
            for _ in range(2):
                mumu12 = available.select(may_mumu12_family=True)
                if mumu12.count == 1:
                    emu_serial = mumu12.first_or_none().serial
                    logger.warning(f'Redirect MuMu12 {self.serial} to {emu_serial}')
                    self.config.Emulator_Serial = self.serial = emu_serial
                    break
                elif mumu12.count >= 2:
                    logger.warning(f'Multiple MuMu12 serial found, cannot redirect')
                    break
                else:
                    # Only 127.0.0.1:7555
                    if self.is_mumu_over_version_356:
                        # is_mumu_over_version_356 and nemud_app_keep_alive was cached
                        # Acceptable since it's the same device
                        logger.warning(f'Device {self.serial} is MuMu12 but corresponding port not found')
                        if IS_WINDOWS:
                            brute_force_connect()
                        devices = self.list_device()
                        # Show available devices
                        available = devices.select(status='device')
                        for device in available:
                            logger.info(device.serial)
                        if not len(available):
                            logger.info('No available devices')
                        continue
                    else:
                        # MuMu6
                        break

        # MuMu12 uses 127.0.0.1:16385 if port 16384 is occupied, auto redirect
        # No config write since it's dynamic
        if self.is_mumu12_family:
            matched = False
            for device in available.select(may_mumu12_family=True):
                if device.port == self.port:
                    # Exact match
                    matched = True
                    break
            if not matched:
                for device in available.select(may_mumu12_family=True):
                    if -2 <= device.port - self.port <= 2:
                        # Port switched
                        logger.info(f'MuMu12 serial switched {self.serial} -> {device.serial}')
                        del_cached_property(self, 'port')
                        del_cached_property(self, 'is_mumu12_family')
                        del_cached_property(self, 'is_mumu_family')
                        self.serial = device.serial
                        break

    @retry
    def list_package(self, show_log=True):
        """
        Find all packages on device.
        Use dumpsys first for faster.
        """
        # 80ms
        if show_log:
            logger.info('Get package list')
        output = self.adb_shell(r'dumpsys package | grep "Package \["')
        packages = re.findall(r'Package \[([^\s]+)\]', output)
        if len(packages):
            return packages

        # 200ms
        if show_log:
            logger.info('Get package list')
        output = self.adb_shell(['pm', 'list', 'packages'])
        packages = re.findall(r'package:([^\s]+)', output)
        return packages

    def list_known_packages(self, show_log=True):
        """
        Args:
            show_log:

        Returns:
            list[str]: List of package names
        """
        packages = self.list_package(show_log=show_log)
        packages = [p for p in packages if p in VALID_PACKAGE or p in VALID_CHANNEL_PACKAGE]
        return packages

    def detect_package(self, set_config=True):
        """
        Show all game client on this device.
        """
        logger.hr('Detect package')
        packages = self.list_known_packages()

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
            logger.critical(f'No AzurLane package found, '
                            f'please confirm AzurLane has been installed on device "{self.serial}"')
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
                f'Multiple AzurLane packages found, auto package detection cannot decide which to choose, '
                'please copy one of the available devices listed above to Alas.Emulator.PackageName')
            raise RequestHumanTakeover
