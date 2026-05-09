import functools
import os
import re
import shutil
import subprocess
import typing as t

# module/device/platform/emulator_base.py
# module/device/platform/emulator_linux.py
# Will be used in Alas Easy Install, they shouldn't import any Alas modules.
from module.device.platform.emulator_base import EmulatorBase, EmulatorInstanceBase, EmulatorManagerBase
from module.device.platform.utils import cached_property, iter_folder


def abspath(path):
    return os.path.abspath(path)


def which(cmd: str) -> t.Optional[str]:
    """
    Find a command in PATH, like shutil.which.

    Args:
        cmd: Command name

    Returns:
        str: Full path to command, or None if not found
    """
    return shutil.which(cmd)


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
            path: Path to emulator binary

        Returns:
            str: Emulator type, or '' if not a recognized emulator
        """
        basename = os.path.basename(path).lower()
        if basename == 'waydroid':
            return cls.Waydroid
        return ''

    @staticmethod
    def multi_to_single(exe: str):
        """
        Waydroid doesn't have a multi-instance manager, yield as-is.
        """
        yield exe

    @staticmethod
    def single_to_console(exe: str):
        """
        Waydroid doesn't have a separate console binary.
        """
        return exe

    @staticmethod
    def _parse_waydroid_prop(prop_path: str) -> t.Dict[str, str]:
        """
        Parse a waydroid.prop file, similar to how MuMu parses vbox configs.

        Args:
            prop_path: Path to waydroid.prop

        Returns:
            dict: Property key-value pairs
        """
        props = {}
        try:
            with open(prop_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, _, value = line.partition('=')
                        props[key.strip()] = value.strip()
        except (FileNotFoundError, PermissionError):
            pass
        return props

    @staticmethod
    def _find_adb_port_from_config(config_dir: str) -> t.Optional[str]:
        """
        Read Waydroid config to find the ADB serial.
        Waydroid uses an LXC bridge network, so the ADB address is the container's IP
        on the waydroid0 bridge, not 127.0.0.1. Default port is 5555.

        Args:
            config_dir: Path to waydroid config directory

        Returns:
            str: serial like '192.168.240.112:5555', or None
        """
        default_port = '5555'
        port = default_port

        # Read waydroid.prop for any port overrides
        prop_path = os.path.join(config_dir, 'waydroid.prop')
        props = Emulator._parse_waydroid_prop(prop_path)

        adb_port = props.get('persist.waydroid.adb.port', '')
        if adb_port and adb_port.isdigit():
            port = adb_port

        # Detect the LXC bridge IP for Waydroid container
        # The container gets DHCP from waydroid0 bridge
        host_ip = Emulator._detect_waydroid_bridge_ip(config_dir)

        if host_ip:
            return f'{host_ip}:{port}'

        # Fallback: try 127.0.0.1 (works with some port-forwarding setups)
        return f'127.0.0.1:{port}'

    @staticmethod
    def _detect_waydroid_bridge_ip(config_dir: str) -> t.Optional[str]:
        """
        Detect the Waydroid container's IP on the waydroid0 bridge.
        The bridge is at 192.168.240.1/24, and the container gets DHCP-assigned IP.

        Strategy:
        1. Check running ADB devices for a device on the waydroid subnet
        2. Fallback: predict bridge subnet + .112 (LXC dnsmasq common default)

        Args:
            config_dir: Waydroid config directory (kept for signature compatibility)

        Returns:
            str: IP address, or None
        """
        bridge_ip = Emulator._get_bridge_ip()
        if not bridge_ip:
            return None

        # Strategy 1: Check running ADB devices on the waydroid bridge subnet
        adb_path = which('adb')
        if adb_path:
            try:
                result = subprocess.run(
                    [adb_path, 'devices'],
                    capture_output=True, text=True, timeout=5
                )
                subnet_prefix = bridge_ip.rsplit('.', 1)[0] + '.'
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if '\tdevice' in line:
                        serial = line.split('\t')[0]
                        if ':' in serial:
                            ip = serial.rsplit(':', 1)[0]
                            if ip.startswith(subnet_prefix):
                                return ip
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass

        # Strategy 2: predict the LXC dnsmasq common default (.112)
        subnet_base = bridge_ip.rsplit('.', 1)[0]
        return f'{subnet_base}.112'

    @staticmethod
    @functools.lru_cache(maxsize=1)
    def _get_bridge_ip() -> t.Optional[str]:
        """
        Get the waydroid0 bridge IP address.
        Works without external commands (compatible with Docker containers).

        Returns:
            str: Bridge IP like '192.168.240.1', or None
        """
        bridge_path = '/sys/class/net/waydroid0'
        if not os.path.exists(bridge_path):
            return None

        # Try `ip` command first
        try:
            result = subprocess.run(
                ['ip', '-4', 'addr', 'show', 'waydroid0'],
                capture_output=True, text=True, timeout=3
            )
            match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', result.stdout)
            if match:
                return match.group(1)
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        # Fallback: parse /proc/net/fib_trie (no external commands needed)
        try:
            with open('/proc/net/fib_trie', 'r') as f:
                content = f.read()
            # Look for waydroid0's local route: /32 host LOCAL under the subnet
            # Match pattern: "192.168.240.1/32 host LOCAL"
            for line in content.split('\n'):
                match = re.search(r'(\d+\.\d+\.\d+\.\d+)/32 host LOCAL', line)
                if match:
                    ip = match.group(1)
                    # Verify this IP is on a waydroid-like subnet
                    if ip.startswith('192.168.'):
                        return ip
        except (FileNotFoundError, PermissionError):
            pass

        return None

    @staticmethod
    def _find_waydroid_adb_serials() -> t.List[str]:
        """
        Find running Waydroid ADB serials without relying on config files.
        Works inside Docker containers where /var/lib/waydroid may be inaccessible.

        Returns:
            list[str]: ADB serials like ['192.168.240.112:5555']
        """
        adb_path = which('adb')
        if not adb_path:
            return []
        try:
            devices = subprocess.run(
                [adb_path, 'devices'],
                capture_output=True, text=True, timeout=5
            )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return []

        serials = []
        for line in devices.stdout.split('\n'):
            line = line.strip()
            if '\tdevice' not in line:
                continue
            serial = line.split('\t')[0]
            try:
                result = subprocess.run(
                    [adb_path, '-s', serial, 'shell', 'getprop', 'ro.product.brand'],
                    capture_output=True, text=True, timeout=5
                )
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                continue
            if 'waydroid' in result.stdout.lower():
                serials.append(serial)
        return serials

    def iter_instances(self) -> t.Iterable[EmulatorInstanceBase]:
        """
        Scan Waydroid config directories for instances, like MuMu scans vms/ folders.
        Falls back to ADB-based detection when config dirs are inaccessible (Docker).

        Yields:
            EmulatorInstance: Waydroid instances found
        """
        if self.type != self.Waydroid:
            return

        config_dirs = EmulatorManager._list_waydroid_config_dirs()
        yielded = False

        for config_dir in config_dirs:
            if not os.path.isdir(config_dir):
                continue

            # Derive instance name from config directory
            # System-wide: 'waydroid', user-specific: 'waydroid-{user}'
            basename = os.path.basename(config_dir)
            if basename == 'waydroid':
                # Check waydroid.prop for host user
                prop_path = os.path.join(config_dir, 'waydroid.prop')
                props = Emulator._parse_waydroid_prop(prop_path)
                host_user = props.get('waydroid.host.user', '')
                if host_user:
                    name = f'waydroid-{host_user}'
                else:
                    name = 'waydroid'
            else:
                name = basename

            # Get ADB serial from config (like MuMu reads vbox port forwarding)
            serial = Emulator._find_adb_port_from_config(config_dir)
            if serial:
                yield EmulatorInstance(
                    serial=serial,
                    name=name,
                    path=self.path
                )
                yielded = True

        # Fallback: ADB-based detection when config dirs are inaccessible (e.g. Docker)
        if not yielded:
            for serial in Emulator._find_waydroid_adb_serials():
                yield EmulatorInstance(
                    serial=serial,
                    name='waydroid',
                    path=self.path
                )

    def iter_adb_binaries(self) -> t.Iterable[str]:
        """
        Find ADB binaries shipped with Waydroid, like MuMu scans for adb_server.exe.

        Yields:
            str: Path to adb binary
        """
        if self.type != self.Waydroid:
            return

        # Waydroid tools directory
        candidates = [
            '/usr/lib/waydroid/tools/adb',
            '/usr/share/waydroid-extra/tools/adb',
            os.path.join(self.dir, 'tools', 'adb'),
        ]

        # Also search in LXC container paths
        for config_dir in EmulatorManager._list_waydroid_config_dirs():
            if os.path.isdir(config_dir):
                # LXC rootfs may contain adb
                rootfs_adb = os.path.join(config_dir, 'rootfs', 'system', 'bin', 'adb')
                if os.path.exists(rootfs_adb):
                    candidates.append(rootfs_adb)

        for path in candidates:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                yield abspath(path)


class EmulatorManager(EmulatorManagerBase):
    # Known waydroid config directory locations
    _WAYDROID_CONFIG_DIRS = [
        '/var/lib/waydroid',
        os.path.expanduser('~/.local/share/waydroid'),
        os.path.expanduser('~/.config/waydroid'),
    ]

    @staticmethod
    def _is_waydroid_config_dir(path: str) -> bool:
        """
        Check if a directory is a valid Waydroid config directory.
        Must contain waydroid.cfg (like MuMu checks for .vbox / .nemu files).

        Returns:
            bool:
        """
        return os.path.isdir(path) and os.path.exists(os.path.join(path, 'waydroid.cfg'))

    @staticmethod
    @functools.lru_cache(maxsize=1)
    def _list_waydroid_config_dirs() -> t.List[str]:
        """
        List all waydroid config directories, including user-specific ones.
        Similar to how MuMu scans multiple vms/ folders.

        Returns:
            list[str]: Paths to waydroid config directories
        """
        dirs = []

        # Standard locations
        for d in EmulatorManager._WAYDROID_CONFIG_DIRS:
            expanded = os.path.expanduser(d)
            if EmulatorManager._is_waydroid_config_dir(expanded):
                dirs.append(abspath(expanded))

        # Scan /var/lib for waydroid-* directories (multi-instance)
        try:
            for entry in os.listdir('/var/lib'):
                if entry.startswith('waydroid') and entry != 'waydroid':
                    full = os.path.join('/var/lib', entry)
                    if EmulatorManager._is_waydroid_config_dir(full):
                        dirs.append(abspath(full))
        except PermissionError:
            pass

        # Scan user home for waydroid-* directories
        for prefix in [
            os.path.expanduser('~/.local/share'),
            os.path.expanduser('~/.config'),
        ]:
            try:
                if not os.path.isdir(prefix):
                    continue
                for entry in os.listdir(prefix):
                    if entry.startswith('waydroid') and entry != 'waydroid':
                        full = os.path.join(prefix, entry)
                        if EmulatorManager._is_waydroid_config_dir(full):
                            dirs.append(abspath(full))
            except PermissionError:
                pass

        return dirs

    @staticmethod
    def _iter_systemd_waydroid_paths() -> t.Iterable[str]:
        """
        Parse waydroid-container systemd service files for ExecStart binary paths.

        Yields:
            str: Absolute path to waydroid binary referenced in a service file
        """
        for service_file in [
            '/usr/lib/systemd/system/waydroid-container.service',
            '/etc/systemd/system/waydroid-container.service',
            os.path.expanduser('~/.config/systemd/user/waydroid-container.service'),
        ]:
            try:
                with open(service_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except (FileNotFoundError, PermissionError):
                continue
            match = re.search(r'ExecStart=(/\S+waydroid\S*)', content)
            if match:
                exec_path = match.group(1).strip()
                if os.path.isfile(exec_path):
                    yield abspath(exec_path)

    @staticmethod
    @functools.lru_cache(maxsize=1)
    def _find_waydroid_binary() -> t.Optional[str]:
        """
        Find the waydroid command, like MuMu searches MuiCache / UserAssist / Uninstall.
        Uses PATH → common locations → systemd service file parsing.

        Returns:
            str: Path to waydroid binary, or None
        """
        # Check PATH (equivalent to scanning MuiCache for exe names)
        path = which('waydroid')
        if path and os.path.isfile(path):
            return abspath(path)

        # Check common installation paths
        candidates = [
            '/usr/bin/waydroid',
            '/usr/local/bin/waydroid',
            '/opt/waydroid/waydroid',
        ]
        for p in candidates:
            if os.path.isfile(p):
                return abspath(p)

        # Try to find from systemd service file (like reading Uninstall registry)
        for exec_path in EmulatorManager._iter_systemd_waydroid_paths():
            return exec_path

        return None

    @staticmethod
    def _find_waydroid_config_dir() -> t.Optional[str]:
        """
        Find primary Waydroid config directory.

        Returns:
            str: Path to waydroid config directory, or None
        """
        # Check known config directories
        candidates = [
            '/var/lib/waydroid',
            os.path.expanduser('~/.local/share/waydroid'),
            os.path.expanduser('~/.config/waydroid'),
        ]
        for p in candidates:
            expanded = os.path.expanduser(p)
            if os.path.isdir(expanded) and os.path.exists(os.path.join(expanded, 'waydroid.cfg')):
                return abspath(expanded)

        return None

    @staticmethod
    def _check_waydroid_status() -> bool:
        """
        Check if Waydroid session is running via the CLI,
        similar to how MuMu checks running processes.

        Returns:
            bool: True if waydroid session is running
        """
        path = which('waydroid')
        if not path:
            return False
        try:
            result = subprocess.run(
                [path, 'status'],
                capture_output=True, text=True, timeout=5
            )
            # Look for "Session: RUNNING"
            if 'RUNNING' in result.stdout:
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        return False

    @staticmethod
    def _check_waydroid_bridge() -> bool:
        """
        Check if the waydroid0 network bridge exists,
        indicating the LXC container is running.

        Returns:
            bool: True if waydroid0 bridge is up
        """
        bridge_path = '/sys/class/net/waydroid0'
        if os.path.exists(bridge_path):
            operstate = os.path.join(bridge_path, 'operstate')
            try:
                with open(operstate, 'r') as f:
                    return f.read().strip() == 'up'
            except (FileNotFoundError, PermissionError):
                pass
        return False

    @staticmethod
    def _check_systemd_service() -> bool:
        """
        Check if waydroid-container systemd service is active.

        Returns:
            bool: True if waydroid-container service is active
        """
        try:
            result = subprocess.run(
                ['systemctl', '--user', 'is-active', 'waydroid-container'],
                capture_output=True, text=True, timeout=5
            )
            if 'active' in result.stdout:
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        return False

    @staticmethod
    def iter_running_emulator():
        """
        Multi-layer running detection, like MuMu's approach:
        1. waydroid status CLI (fastest)
        2. waydroid0 network bridge
        3. systemd service
        4. /proc or psutil process scanning

        Yields:
            str: Path to waydroid binary if running
        """
        path = which('waydroid')

        # Layer 1: waydroid status CLI
        if EmulatorManager._check_waydroid_status():
            if path:
                yield abspath(path)
            return

        # Layer 2: waydroid0 bridge
        if EmulatorManager._check_waydroid_bridge():
            if path:
                yield abspath(path)
            return

        # Layer 3: systemd service
        if EmulatorManager._check_systemd_service():
            if path:
                yield abspath(path)
            return

        # Layer 4: process scanning (/proc or psutil)
        try:
            import psutil
        except ModuleNotFoundError:
            # Fallback: check for waydroid process via /proc
            for pid in os.listdir('/proc'):
                if not pid.isdigit():
                    continue
                try:
                    cmdline_path = f'/proc/{pid}/cmdline'
                    with open(cmdline_path, 'rb') as f:
                        raw = f.read()
                    cmdline = raw.decode('utf-8', errors='replace')
                    # Look for waydroid container process
                    if 'waydroid' in cmdline.lower() and 'container' in cmdline.lower():
                        if path:
                            yield abspath(path)
                        return
                except (FileNotFoundError, PermissionError, OSError):
                    continue
            return

        # psutil fallback
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline') or []
                cmdline_str = ' '.join(cmdline) if cmdline else ''
                name = (proc.info.get('name') or '').lower()
                if 'waydroid' in cmdline_str.lower() or name == 'waydroid':
                    if path:
                        yield abspath(path)
                    return
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    @cached_property
    def all_emulators(self) -> t.List[Emulator]:
        """
        Get all Waydroid installations, like MuMu's all_emulators scans:
        1. Binary in PATH
        2. Config directories
        3. systemd service files
        4. Running processes
        """
        exe = set()

        # Source 1: PATH / common locations
        path = self._find_waydroid_binary()
        if path and Emulator.is_emulator(path):
            exe.add(path)

        # Source 2: Config directories (may find waydroid even if binary not in PATH)
        for config_dir in self._list_waydroid_config_dirs():
            if not os.path.isdir(config_dir):
                continue
            # Look for waydroid binary relative to config
            parent = os.path.dirname(config_dir)
            for candidate in [
                os.path.join(parent, 'waydroid'),
                '/usr/bin/waydroid',
            ]:
                if os.path.isfile(candidate) and Emulator.is_emulator(candidate):
                    exe.add(abspath(candidate))

        # Source 3: systemd service files (like scanning Uninstall registry)
        for exec_path in self._iter_systemd_waydroid_paths():
            if Emulator.is_emulator(exec_path):
                exe.add(exec_path)

        # Source 4: Running processes
        for file in self.iter_running_emulator():
            if os.path.isfile(file):
                exe.add(file)

        return [Emulator(path) for path in exe]

    @cached_property
    def all_emulator_instances(self) -> t.List[EmulatorInstance]:
        """
        Get all Waydroid instances, deduplicated by (serial, name).
        """
        instances = []
        for emulator in self.all_emulators:
            instances += list(emulator.iter_instances())

        # Dedup by (serial, name) — like MuMu avoids duplicate instances
        seen = set()
        unique = []
        for inst in instances:
            key = (inst.serial, inst.name)
            if key not in seen:
                seen.add(key)
                unique.append(inst)

        instances: t.List[EmulatorInstance] = sorted(unique, key=lambda x: str(x))
        return instances


if __name__ == '__main__':
    self = EmulatorManager()
    for emu in self.all_emulator_instances:
        print(emu)
