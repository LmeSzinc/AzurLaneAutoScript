import socket
from functools import wraps

from adbutils.errors import AdbError

from module.base.decorator import cached_property, del_cached_property
from module.base.timer import Timer
from module.base.utils import *
from module.device.connection import Connection
from module.device.method.minitouch import CommandBuilder, insert_swipe
from module.device.method.utils import RETRY_TRIES, retry_sleep, handle_adb_error
from module.exception import RequestHumanTakeover
from module.logger import logger


def retry(func):
    @wraps(func)
    def retry_wrapper(self, *args, **kwargs):
        """
        Args:
            self (MaaTouch):
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
                    del_cached_property(self, 'maatouch_builder')
            # Emulator closed
            except ConnectionAbortedError as e:
                logger.error(e)

                def init():
                    self.adb_reconnect()
                    del_cached_property(self, 'maatouch_builder')
            # AdbError
            except AdbError as e:
                if handle_adb_error(e):
                    def init():
                        self.adb_reconnect()
                        del_cached_property(self, 'maatouch_builder')
                else:
                    break
            # MaaTouchNotInstalledError: Received "Aborted" from MaaTouch
            except MaaTouchNotInstalledError as e:
                logger.error(e)

                def init():
                    self.maatouch_install()
                    del_cached_property(self, 'maatouch_builder')
            except BrokenPipeError as e:
                logger.error(e)

                def init():
                    del_cached_property(self, 'maatouch_builder')
            # Unknown, probably a trucked image
            except Exception as e:
                logger.exception(e)

                def init():
                    pass

        logger.critical(f'Retry {func.__name__}() failed')
        raise RequestHumanTakeover

    return retry_wrapper


class MaaTouchNotInstalledError(Exception):
    pass


class MaaTouch(Connection):
    """
    Control method that implements the same as scrcpy and has an interface similar to minitouch.
    https://github.com/MaaAssistantArknights/MaaTouch
    """
    max_x: int
    max_y: int
    _maatouch_stream = socket.socket
    _maatouch_stream_storage = None

    @cached_property
    def maatouch_builder(self):
        self.maatouch_init()
        return CommandBuilder(self)

    def maatouch_init(self):
        logger.hr('MaaTouch init')
        max_x, max_y = 1280, 720
        max_contacts = 2
        max_pressure = 50

        # CLASSPATH=/data/local/tmp/maatouch app_process / com.shxyke.MaaTouch.App
        stream = self.adb_shell(
            ['CLASSPATH=/data/local/tmp/maatouch', 'app_process', '/', 'com.shxyke.MaaTouch.App'],
            stream=True,
            recvall=False
        )
        # Prevent shell stream from being deleted causing socket close
        self._maatouch_stream_storage = stream
        stream = stream.conn
        stream.settimeout(10)
        self._maatouch_stream = stream

        retry_timeout = Timer(5).start()
        while 1:
            # v <version>
            # protocol version, usually it is 1. needn't use this
            # get maatouch server info
            socket_out = stream.makefile()

            # ^ <max-contacts> <max-x> <max-y> <max-pressure>
            out = socket_out.readline().replace("\n", "").replace("\r", "")
            logger.info(out)
            if out.strip() == 'Aborted':
                stream.close()
                raise MaaTouchNotInstalledError(
                    'Received "Aborted" MaaTouch, '
                    'probably because MaaTouch is not installed'
                )
            try:
                _, max_contacts, max_x, max_y, max_pressure = out.split(" ")
                break
            except ValueError:
                stream.close()
                if retry_timeout.reached():
                    raise MaaTouchNotInstalledError(
                        'Received empty data from MaaTouch, '
                        'probably because MaaTouch is not installed'
                    )
                else:
                    # maatouch may not start that fast
                    self.sleep(1)
                    continue

        # self.max_contacts = max_contacts
        self.max_x = int(max_x)
        self.max_y = int(max_y)
        # self.max_pressure = max_pressure

        # $ <pid>
        out = socket_out.readline().replace("\n", "").replace("\r", "")
        logger.info(out)
        # _, pid = out.split(" ")
        # self._maatouch_pid = pid

        logger.info(
            "MaaTouch stream connected"
        )
        logger.info(
            "max_contact: {}; max_x: {}; max_y: {}; max_pressure: {}".format(
                max_contacts, max_x, max_y, max_pressure
            )
        )

    def maatouch_send(self):
        content = self.maatouch_builder.to_minitouch()
        # logger.info("send operation: {}".format(content.replace("\n", "\\n")))
        byte_content = content.encode('utf-8')
        self._maatouch_stream.sendall(byte_content)
        self._maatouch_stream.recv(0)
        self.sleep(self.maatouch_builder.delay / 1000 + self.maatouch_builder.DEFAULT_DELAY)
        self.maatouch_builder.clear()

    def maatouch_install(self):
        logger.hr('MaaTouch install')
        self.adb_push(self.config.MAATOUCH_FILEPATH_LOCAL, self.config.MAATOUCH_FILEPATH_REMOTE)

    def maatouch_uninstall(self):
        logger.hr('MaaTouch uninstall')
        self.adb_shell(["rm", self.config.MAATOUCH_FILEPATH_REMOTE])

    @retry
    def click_maatouch(self, x, y):
        builder = self.maatouch_builder
        builder.down(x, y).commit()
        builder.up().commit()
        self.maatouch_send()

    @retry
    def long_click_maatouch(self, x, y, duration=1.0):
        duration = int(duration * 1000)
        builder = self.maatouch_builder
        builder.down(x, y).commit().wait(duration)
        builder.up().commit()
        self.maatouch_send()

    @retry
    def swipe_maatouch(self, p1, p2):
        points = insert_swipe(p0=p1, p3=p2)
        builder = self.maatouch_builder

        builder.down(*points[0]).commit()
        self.maatouch_send()

        for point in points[1:]:
            builder.move(*point).commit().wait(10)
        self.maatouch_send()

        builder.up().commit()
        self.maatouch_send()

    @retry
    def drag_maatouch(self, p1, p2, point_random=(-10, -10, 10, 10)):
        p1 = np.array(p1) - random_rectangle_point(point_random)
        p2 = np.array(p2) - random_rectangle_point(point_random)
        points = insert_swipe(p0=p1, p3=p2, speed=20)
        builder = self.maatouch_builder

        builder.down(*points[0]).commit()
        self.maatouch_send()

        for point in points[1:]:
            builder.move(*point).commit().wait(10)
        self.maatouch_send()

        builder.move(*p2).commit().wait(140)
        builder.move(*p2).commit().wait(140)
        self.maatouch_send()

        builder.up().commit()
        self.maatouch_send()
