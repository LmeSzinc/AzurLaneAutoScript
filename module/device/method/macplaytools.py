import socket
import struct
import subprocess
import threading
import time
import cv2
import numpy as np
from functools import wraps

from module.base.decorator import cached_property, del_cached_property, has_cached_property
from module.base.timer import Timer
from module.base.utils import *
from module.device.connection import Connection
from module.device.method.minitouch import insert_swipe
from module.device.method.utils import RETRY_TRIES, retry_sleep
from module.exception import RequestHumanTakeover
from module.logger import logger

def retry(func):
    @wraps(func)
    def retry_wrapper(self, *args, **kwargs):
        """
        Args:
            self (MacPlayTools):
        """
        init = None
        for _ in range(RETRY_TRIES):
            try:
                if callable(init):
                    time.sleep(retry_sleep(_))
                    init()
                return func(self, *args, **kwargs)
            # Can't handle
            except RequestHumanTakeover:
                break
            # Just wait until it ready
            except ScreenshotNotConnected:
                time.sleep(2)
            # When azurlane was not launched
            except ConnectionRefusedError as e:
                logger.error(e)
                logger.error("possibly game not running.")
                break
            # When azurlane was killed
            except ConnectionResetError as e:
                logger.error(e)

                def init():
                    del_cached_property(self, '_macplaytools_builder')
            except ConnectionAbortedError as e:
                logger.error(e)

                def init():
                    del_cached_property(self, '_macplaytools_builder')
            except BrokenPipeError as e:
                logger.error(e)

                def init():
                    del_cached_property(self, '_macplaytools_builder')
            # Unknown, probably a trucked image
            except Exception as e:
                logger.exception(e)
                def init():
                    pass

        logger.critical(f'Retry {func.__name__}() failed')
        raise RequestHumanTakeover

    return retry_wrapper


# availble commands of macplaytools

CMD_HANDSHAKE = b'MAA\x00' # returns char[4] b'OKAY'
CMD_TERM = b'\x00\x04TERM' # no return
CMD_VERSION = b'\x00\x04VERN' # returns uint32_t version
CMD_SCREENSIZE = b'\x00\x04SIZE' # returns uint16_t width and uint16_t height
CMD_SCREENCAP = b'\x00\x04SCRN' # returns uint32_t size and char[size] image(RGBA raw)
CMD_TOUCH = b'\x00\x09TUCH' 
# no return,send char[6] CMD_TOUCH,uint8_t TouchPhase,uint16_t h,uint16_t w

# TouchPhase of touch command

TOUCHPHASE_BEGAN = b'\x00'
TOUCHPHASE_MOVED = b'\x01'
TOUCHPHASE_ENDED = b'\x03'


class MacplaytoolsBuilder:
    """
    Build and send binary command data for MacPlayTools protocol.
    Each touch command (down/move/up) is sent immediately via the device stream.
    Wait delays are handled inline with time.sleep.

    Available commands in MacPlayTools protocol:
      CMD_TOUCH (b'\\x00\\x09TUCH') - Touch event with:
        TOUCHPHASE_BEGAN (b'\\x00') - Finger down
        TOUCHPHASE_MOVED (b'\\x01') - Finger move
        TOUCHPHASE_ENDED (b'\\x03') - Finger up
      Format: struct.pack(">6ssHH", CMD_TOUCH, phase, h, w)
    """
    DEFAULT_DELAY = 0.05
    max_x = 1280
    max_y = 720

    def __init__(self, device, contact=0):
        """
        Args:
            device (MacPlayTools):
        """
        self.device = device
        self.contact = 0 # macplaytools only support single-touch

    def down(self, x, y):
        """Send touch down (BEGAN) immediately."""
        self.device.send_touch(TOUCHPHASE_BEGAN, x, y)
        return self

    def move(self, x, y):
        """Send touch move (MOVED) immediately."""
        self.device.send_touch(TOUCHPHASE_MOVED, x, y)
        return self

    def up(self, x, y):
        """Send touch up (ENDED) immediately."""
        self.device.send_touch(TOUCHPHASE_ENDED, x, y)
        return self

    def wait(self, ms=10):
        """Handle wait delay inline (MacPlayTools cannot process wait commands)."""
        time.sleep(ms / 1000)
        return self
    
    def end(self):
        """Final sleep after all operations."""
        self.device.sleep(self.DEFAULT_DELAY)


class MacConnection(Connection):
    """
    Connection subclass for MacPlayTools environment where ADB is not available.
    All adb_* methods are overridden to log a warning and do nothing.
    """

    _ADB_UNAVAILABLE_MSG = "ADB not available in MacPlayTools environment,no action taken."

    def adb_command(self, cmd, timeout=10):
        logger.warning(self._ADB_UNAVAILABLE_MSG)
        return ''

    def adb_start_server(self):
        logger.warning(self._ADB_UNAVAILABLE_MSG)
        return ''

    def adb_shell(self, cmd, stream=False, recvall=True, timeout=10, rstrip=True):
        logger.warning(self._ADB_UNAVAILABLE_MSG)
        if stream:
            return b''
        return ''

    def adb_getprop(self, name):
        logger.warning(self._ADB_UNAVAILABLE_MSG)
        return ''

    def adb_shell_nc(self, cmd, timeout=5, chunk_size=262144):
        logger.warning(self._ADB_UNAVAILABLE_MSG)
        return b''

    def adb_exec_out(self, cmd, serial=None):
        logger.warning(self._ADB_UNAVAILABLE_MSG)
        return ''

    def adb_forward(self, remote):
        logger.warning(self._ADB_UNAVAILABLE_MSG)
        return 0

    def adb_reverse(self, remote):
        logger.warning(self._ADB_UNAVAILABLE_MSG)
        return 0

    def adb_forward_remove(self, local):
        logger.warning(self._ADB_UNAVAILABLE_MSG)

    def adb_reverse_remove(self, local):
        logger.warning(self._ADB_UNAVAILABLE_MSG)

    def adb_push(self, local, remote):
        logger.warning(self._ADB_UNAVAILABLE_MSG)
        return ''

    def adb_connect(self, wait_device=True):
        logger.info(self._ADB_UNAVAILABLE_MSG)
        return True

    def adb_brute_force_connect(self, serial_list):
        logger.info(self._ADB_UNAVAILABLE_MSG)

    def adb_disconnect(self):
        logger.info(self._ADB_UNAVAILABLE_MSG)

    def adb_restart(self):
        logger.info(self._ADB_UNAVAILABLE_MSG)

    def adb_reconnect(self):
        logger.info(self._ADB_UNAVAILABLE_MSG)


class ScreenshotNotConnected(Exception):
    pass


class MacPlayTools(MacConnection):
    """
    Control method that implements the same as scrcpy and has an interface similar to minitouch.
    https://github.com/hguandl/PlayCover
    """
    max_x: int
    max_y: int
    _macplaytools_client: socket.socket = None
    _macplaytools_client_screenshot: socket.socket = None
    _macplaytools_init_thread = None

    @cached_property
    @retry
    def _macplaytools_builder(self):
        self.macplaytools_init()
        return MacplaytoolsBuilder(self)

    @staticmethod
    def _recvall(sock, n) -> bytes:
        data = b''
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                break
            data += packet
        return data

    @property
    def macplaytools_builder(self):
        # Wait init thread
        if self._macplaytools_init_thread is not None:
            self._macplaytools_init_thread.join()
            del self._macplaytools_init_thread
            self._macplaytools_init_thread = None

        return self._macplaytools_builder

    def early_macplaytools_init(self):
        """
        Start a thread to init macplaytools connection while the Alas instance just starting to take screenshots
        This would speed up the first click 0.2 ~ 0.4s.
        """
        if has_cached_property(self, '_macplaytools_builder'):
            return

        def early_macplaytools_init_func():
            _ = self._macplaytools_builder

        thread = threading.Thread(target=early_macplaytools_init_func, daemon=True)
        self._macplaytools_init_thread = thread
        thread.start()

    def macplaytools_init(self):
        logger.hr('MacPlayTools init')

        # Try to close existing client
        if self._macplaytools_client is not None:
            try:
                self._macplaytools_client.close()
            except Exception as e:
                logger.error(e)
            del self._macplaytools_client


        if self._macplaytools_client_screenshot is not None:
            try:
                self._macplaytools_client_screenshot.close()
            except Exception as e:
                logger.error(e)
            del self._macplaytools_client_screenshot

        while 1:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            screenshot = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            client.settimeout(1)
            screenshot.settimeout(1)

            addr, port = self.serial.rsplit(':', 1)
            client.connect((addr, int(port)))
            screenshot.connect((addr, int(port)))

            self._macplaytools_client = client
            self._macplaytools_client_screenshot = screenshot

            # send handshake on both connections
            client.sendall(CMD_HANDSHAKE)
            screenshot.sendall(CMD_HANDSHAKE)

            if client.recv(4) == b'OKAY' and screenshot.recv(4) == b'OKAY':
                break

        # query resolution on touch client
        client.sendall(CMD_SCREENSIZE)
        self.max_x, self.max_y = struct.unpack(">HH", client.recv(4))

        # query version
        client.sendall(CMD_VERSION)
        version = int.from_bytes(client.recv(4), byteorder='big', signed=False)

        # query resolution on screenshot client
        screenshot.sendall(CMD_SCREENSIZE)
        screenshot.recv(4)

        screenshot.settimeout(2)
        client.settimeout(2)
        
        logger.info(
            "MacPlayTools client connected, protocol version: {}".format(version)
        )
        logger.info(
            "max_contact: 0; max_x: {}; max_y: {}".format(
                self.max_x, self.max_y
            )
        )

    def send_touch(self, phase, x=0, y=0):
        """Pack and send a touch command immediately via the device stream."""
        data = struct.pack(">6ssHH", CMD_TOUCH, phase, x, y)
        self._macplaytools_client.sendall(data)
        self._macplaytools_client.recv(0)

    def macplaytools_install(self):
        pass

    def macplaytools_uninstall(self):
        pass

    @retry
    def screenshot_macplaytools(self):
        client = self._macplaytools_client_screenshot
        if client == None:
            raise ScreenshotNotConnected
        client.sendall(CMD_SCREENCAP)

        # get length of image
        recv = client.recv(4)
        length = int.from_bytes(recv, byteorder="big", signed=False)
        image = self._recvall(client, length)
        image = np.frombuffer(image, dtype=np.uint8).reshape((self.max_y, self.max_x, 4))
        # RGBA2RGB
        return image[:, :, :3]

    @retry
    def click_macplaytools(self, x, y):
        builder = self.macplaytools_builder
        builder.down(x, y)
        builder.up(x, y)

    @retry
    def long_click_macplaytools(self, x, y, duration=1.0):
        duration = int(duration * 1000)
        builder = self.macplaytools_builder
        builder.down(x, y).wait(duration)
        builder.up(x, y)

    @retry
    def swipe_macplaytools(self, p1, p2):
        points = insert_swipe(p0=p1, p3=p2)
        builder = self.macplaytools_builder

        builder.down(*points[0]).wait(10)

        for point in points[1:]:
            builder.move(*point).wait(10)

        builder.up(*points[-1])

    @retry
    def drag_macplaytools(self, p1, p2, point_random=(-10, -10, 10, 10)):
        p1 = np.array(p1) - random_rectangle_point(point_random)
        p2 = np.array(p2) - random_rectangle_point(point_random)
        points = insert_swipe(p0=p1, p3=p2, speed=20)
        builder = self.macplaytools_builder

        builder.down(*points[0]).wait(10)

        for point in points[1:]:
            builder.move(*point).wait(10)

        builder.move(*p2).wait(140)
        builder.move(*p2).wait(140)

        builder.up(*p2)
