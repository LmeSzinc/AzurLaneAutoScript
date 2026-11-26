import os
import re
import shutil
import typing as t

# module/device/platform/emulator_base.py
# module/device/platform/emulator_linux.py
# Will be used in Alas Easy Install, they shouldn't import any Alas modules.
from module.device.platform.emulator_base import EmulatorBase, EmulatorInstanceBase, EmulatorManagerBase
from module.device.platform.utils import cached_property

WAYDROID_BRIDGE = 'waydroid0'
# Default container IP assigned by waydroid-net.sh
WAYDROID_DEFAULT_IP = '192.168.240.112'
WAYDROID_DEFAULT_PORT = '5555'


def abspath(path):
    return os.path.abspath(path)


def read_file(file: str) -> str:
    """
    Returns:
        str: File content, or '' if file not readable
    """
    try:
        with open(file, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except (FileNotFoundError, PermissionError, OSError):
        return ''


def is_waydroid_config_dir(path: str) -> bool:
    """
    A valid Waydroid config directory must contain waydroid.cfg
    """
    return os.path.isfile(os.path.join(path, 'waydroid.cfg'))


def iter_waydroid_config_dirs() -> t.Iterable[str]:
    """
    Yields:
        str: Absolute path to waydroid config directories, including multi-instance ones like `waydroid-xxx`
    """
    for parent in [
        '/var/lib',
        os.path.expanduser('~/.local/share'),
        os.path.expanduser('~/.config'),
    ]:
        try:
            entries = sorted(os.listdir(parent))
        except (FileNotFoundError, PermissionError, OSError):
            continue
        for entry in entries:
            if not entry.startswith('waydroid'):
                continue
            path = os.path.join(parent, entry)
            if is_waydroid_config_dir(path):
                yield abspath(path)


def parse_prop(file: str) -> t.Dict[str, str]:
    """
    Parse `key=value` lines from a waydroid.prop file.
    """
    props = {}
    for line in read_file(file).splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        key, sep, value = line.partition('=')
        if sep:
            props[key.strip()] = value.strip()
    return props


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

    @cached_property
    def bridge_ip(self) -> t.Optional[str]:
        """
        IPv4 address of the waydroid0 bridge on host, read from /proc/net/fib_trie.

        Returns:
            str: Bridge IP like '192.168.240.1', or None if bridge not exists
        """
        if not os.path.exists(f'/sys/class/net/{WAYDROID_BRIDGE}'):
            return None
        # Local addresses are listed as "|-- 192.168.240.1" followed by "/32 host LOCAL"
        content = read_file('/proc/net/fib_trie')
        for ip in re.findall(r'\|-- (\d+\.\d+\.\d+\.\d+)\s+/32 host LOCAL', content):
            if ip.startswith('192.168.240.'):
                return ip
        return None

    @cached_property
    def container_ip(self) -> t.Optional[str]:
        """
        IPv4 address of the Waydroid container on the waydroid0 bridge.
        Read from system environment only, no adb commands, because emulator detection
        decides which serial adb should connect to.

        1. DHCP lease file written by dnsmasq in waydroid-net.sh
        2. ARP table entries on waydroid0
        3. Default IP if bridge exists

        Returns:
            str: Container IP like '192.168.240.112', or None
        """
        # 1700000000 00:16:3e:f9:d3:03 192.168.240.112 WayDroid-x86-64-Device 01:00:16:3e:f9:d3:03
        content = read_file(f'/var/lib/misc/dnsmasq.{WAYDROID_BRIDGE}.leases')
        for line in content.splitlines():
            parts = line.split()
            if len(parts) >= 3 and re.fullmatch(r'\d+\.\d+\.\d+\.\d+', parts[2]):
                return parts[2]

        # IP address       HW type     Flags       HW address            Mask     Device
        # 192.168.240.112  0x1         0x2         00:16:3e:f9:d3:03     *        waydroid0
        content = read_file('/proc/net/arp')
        for line in content.splitlines()[1:]:
            parts = line.split()
            # Flags 0x0 means incomplete entry
            if len(parts) >= 6 and parts[5] == WAYDROID_BRIDGE and parts[2] != '0x0':
                return parts[0]

        if self.bridge_ip:
            return WAYDROID_DEFAULT_IP
        return None

    def config_dir_to_serial(self, config_dir: str) -> t.Optional[str]:
        """
        Args:
            config_dir: Waydroid config directory

        Returns:
            str: Serial like '192.168.240.112:5555', or None
        """
        props = parse_prop(os.path.join(config_dir, 'waydroid.prop'))
        port = props.get('persist.waydroid.adb.port', '')
        if not port.isdigit():
            port = WAYDROID_DEFAULT_PORT

        ip = self.container_ip
        if ip:
            return f'{ip}:{port}'
        return None

    @staticmethod
    def config_dir_to_name(config_dir: str) -> str:
        """
        System-wide: 'waydroid', user-specific: 'waydroid-{user}'
        """
        basename = os.path.basename(config_dir)
        if basename != 'waydroid':
            return basename
        props = parse_prop(os.path.join(config_dir, 'waydroid.prop'))
        host_user = props.get('waydroid.host.user', '')
        if host_user:
            return f'waydroid-{host_user}'
        return 'waydroid'

    def iter_instances(self) -> t.Iterable[EmulatorInstance]:
        """
        Yields:
            EmulatorInstance: Waydroid instances found
        """
        if self.type != self.Waydroid:
            return

        yielded = False
        for config_dir in iter_waydroid_config_dirs():
            serial = self.config_dir_to_serial(config_dir)
            if serial:
                yield EmulatorInstance(
                    serial=serial,
                    name=self.config_dir_to_name(config_dir),
                    path=self.path,
                )
                yielded = True

        # Config directories may be inaccessible, e.g. in docker with host network mode
        if not yielded and self.container_ip:
            yield EmulatorInstance(
                serial=f'{self.container_ip}:{WAYDROID_DEFAULT_PORT}',
                name='waydroid',
                path=self.path,
            )

    def iter_adb_binaries(self) -> t.Iterable[str]:
        """
        Yields:
            str: Path to adb binary shipped with Waydroid
        """
        if self.type != self.Waydroid:
            return

        for path in [
            '/usr/lib/waydroid/tools/adb',
            '/usr/share/waydroid-extra/tools/adb',
            os.path.join(self.dir, 'tools', 'adb'),
        ]:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                yield abspath(path)


class EmulatorManager(EmulatorManagerBase):
    @staticmethod
    def iter_systemd_waydroid_paths() -> t.Iterable[str]:
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
            content = read_file(service_file)
            res = re.search(r'ExecStart=(/\S*waydroid)\b', content)
            if res and os.path.isfile(res.group(1)):
                yield abspath(res.group(1))

    @cached_property
    def waydroid_binary(self) -> t.Optional[str]:
        """
        Returns:
            str: Path to waydroid binary, or None
        """
        path = shutil.which('waydroid')
        if path and os.path.isfile(path):
            return abspath(path)
        for path in [
            '/usr/bin/waydroid',
            '/usr/local/bin/waydroid',
        ]:
            if os.path.isfile(path):
                return abspath(path)
        return None

    @staticmethod
    def iter_running_emulator():
        """
        Yields:
            str: Path to waydroid binary from running processes, may contains duplicate values
        """
        try:
            import psutil
        except ModuleNotFoundError:
            return
        for proc in psutil.process_iter(['cmdline']):
            cmdline = proc.info.get('cmdline') or []
            # Waydroid is a python script, cmdline is like:
            # ['/usr/bin/python3', '/usr/bin/waydroid', '-w', 'container', 'start']
            for arg in cmdline[:2]:
                if Emulator.is_emulator(arg) and os.path.isabs(arg):
                    yield arg

    @cached_property
    def all_emulators(self) -> t.List[Emulator]:
        """
        Get all Waydroid installations.
        """
        exe = set()

        # PATH and common locations
        if self.waydroid_binary:
            exe.add(self.waydroid_binary)

        # systemd service files
        for file in self.iter_systemd_waydroid_paths():
            exe.add(file)

        # Running
        for file in self.iter_running_emulator():
            if os.path.isfile(file):
                exe.add(abspath(file))

        return [Emulator(path) for path in sorted(exe) if Emulator.is_emulator(path)]

    @cached_property
    def all_emulator_instances(self) -> t.List[EmulatorInstance]:
        """
        Get all Waydroid instances, deduplicated by (serial, name).
        """
        unique = {}
        for emulator in self.all_emulators:
            for instance in emulator.iter_instances():
                unique[(instance.serial, instance.name)] = instance

        instances: t.List[EmulatorInstance] = sorted(unique.values(), key=lambda x: str(x))
        return instances


if __name__ == '__main__':
    self = EmulatorManager()
    for emu in self.all_emulator_instances:
        print(emu)
