import random
import socket

from module.logger import logger
import uiautomator2 as u2


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


def possible_reasons(*args):
    """
    Show possible reasons

        Possible reason #1: <reason_1>
        Possible reason #2: <reason_2>
    """
    for index, reason in enumerate(args):
        index += 1
        logger.critical(f'Possible reason #{index}: {reason}')


def handle_adb_error(e):
    # AdbError(closed)
    # AdbError(device offline)
    # AdbError(device '127.0.0.1:59865' not found)
    # AdbError()
    logger.exception(e)
    possible_reasons(
        'If you are using BlueStacks or LD player, please enable ADB in the settings of your emulator',
        'Emulator died, please restart emulator',
        'Serial incorrect, no such device exists or emulator is not running'
    )


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
