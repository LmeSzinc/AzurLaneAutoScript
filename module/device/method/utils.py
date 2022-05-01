import random
import re
import socket

import uiautomator2 as u2
from adbutils import AdbTimeout, _AdbStreamConnection
from lxml import etree

from module.base.decorator import cached_property
from module.logger import logger

RETRY_TRIES = 5
RETRY_DELAY = 3


def is_port_using(port_num):
    """ if port is using by others, return True. else return False """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)

    try:
        result = s.connect_ex(('127.0.0.1', port_num))
        # if port is using, return code should be 0. (can be connected)
        return result == 0
    finally:
        s.close()


def random_port(port_range):
    """ get a random port from port set """
    new_port = random.choice(list(range(*port_range)))
    if is_port_using(new_port):
        return random_port(port_range)
    else:
        return new_port


def recv_all(stream, chunk_size=4096) -> bytes:
    """
    Args:
        stream:
        chunk_size:

    Returns:
        bytes:

    Raises:
        AdbTimeout
    """
    if isinstance(stream, _AdbStreamConnection):
        stream = stream.conn
        stream.settimeout(10)

    try:
        fragments = []
        while 1:
            chunk = stream.recv(chunk_size)
            if chunk:
                fragments.append(chunk)
            else:
                break
        return b''.join(fragments)
    except socket.timeout:
        raise AdbTimeout('adb read timeout')


def possible_reasons(*args):
    """
    Show possible reasons

        Possible reason #1: <reason_1>
        Possible reason #2: <reason_2>
    """
    for index, reason in enumerate(args):
        index += 1
        logger.critical(f'Possible reason #{index}: {reason}')


class PackageNotInstalled(Exception):
    pass


def handle_adb_error(e):
    """
    Args:
        e (Exception):

    Returns:
        bool: If should retry
    """
    text = str(e)
    if 'not found' in text:
        # When you call `adb disconnect <serial>`
        # Or when adb server was killed (low possibility)
        # AdbError(device '127.0.0.1:59865' not found)
        logger.error(e)
        return True
    elif 'timeout' in text:
        # AdbTimeout(adb read timeout)
        logger.error(e)
        return True
    elif 'closed' in text:
        # AdbError(closed)
        # Usually after AdbTimeout(adb read timeout)
        # Disconnect and re-connect should fix this.
        logger.error(e)
        return True
    elif 'device offline' in text:
        # AdbError(device offline)
        # When a device that has been connected wirelessly is disconnected passively,
        # it does not disappear from the adb device list,
        # but will be displayed as offline.
        # In many cases, such as disconnection and recovery caused by network fluctuations,
        # or after VMOS reboot when running Alas on a phone,
        # the device is still available, but it needs to be disconnected and re-connected.
        logger.error(e)
        return True
    elif 'unknown host service' in text:
        # AdbError(unknown host service)
        # Another version of ADB service started, current ADB service has been killed.
        # Usually because user opened a Chinese emulator, which uses ADB from the Stone Age.
        logger.error(e)
        return True
    else:
        # AdbError()
        logger.exception(e)
        possible_reasons(
            'If you are using BlueStacks or LD player or WSA, please enable ADB in the settings of your emulator',
            'Emulator died, please restart emulator',
            'Serial incorrect, no such device exists or emulator is not running'
        )
        return False


def del_cached_property(obj, name):
    """
    Delete a cached property safely.

    Args:
        obj:
        name (str):
    """
    if name in obj.__dict__:
        del obj.__dict__[name]


class IniterNoMinicap(u2.init.Initer):
    @property
    def minicap_urls(self):
        """
        binary from https://github.com/openatx/stf-binaries
        only got abi: armeabi-v7a and arm64-v8a
        """
        return []


# Monkey patch, don't install minicap on emulators
u2.init.Initer = IniterNoMinicap


class HierarchyButton:
    """
    Convert UI hierarchy to an object like the Button in Alas.
    """
    _name_regex = re.compile('@.*?=[\'\"](.*?)[\'\"]')

    def __init__(self, hierarchy: etree._Element, xpath: str):
        self.hierarchy = hierarchy
        self.xpath = xpath
        self.nodes = hierarchy.xpath(xpath)

    @cached_property
    def name(self):
        res = HierarchyButton._name_regex.findall(self.xpath)
        if res:
            return res[0]
        else:
            return 'HierarchyButton'

    @cached_property
    def count(self):
        return len(self.nodes)

    @cached_property
    def exist(self):
        return self.count == 1

    @cached_property
    def area(self):
        if self.exist:
            bounds = self.nodes[0].attrib.get("bounds")
            lx, ly, rx, ry = map(int, re.findall(r"\d+", bounds))
            return lx, ly, rx, ry
        else:
            return None

    @cached_property
    def button(self):
        return self.area

    def __bool__(self):
        return self.exist

    def __str__(self):
        return self.name

    @cached_property
    def focused(self):
        if self.exist:
            return self.nodes[0].attrib.get("focused").lower() == 'true'
        else:
            return False
