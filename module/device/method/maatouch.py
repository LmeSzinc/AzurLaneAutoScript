import socket
import threading
import time
from functools import wraps

from adbutils.errors import AdbError

from module.base.decorator import cached_property, del_cached_property, has_cached_property
from module.base.timer import Timer
from module.base.utils import *
from module.device.connection import Connection
from module.device.method.minitouch import Command, CommandBuilder, insert_swipe
from module.device.method.utils import RETRY_TRIES, handle_adb_error, retry_sleep
from module.exception import RequestHumanTakeover
from module.logger import logger


def handle_unknown_host_service(e):
    pass


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
                    time.sleep(retry_sleep(_))
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
                    del_cached_property(self, '_maatouch_builder')
            # MaaTouchSyncTimeout
            # Probably because adb server was killed
            except MaaTouchSyncTimeout as e:
                logger.error(e)

                def init():
                    self.adb_reconnect()
                    del_cached_property(self, '_maatouch_builder')
                    self.reset_maatouch()
            # Emulator closed
            except ConnectionAbortedError as e:
                logger.error(e)

                def init():
                    self.adb_reconnect()
                    del_cached_property(self, '_maatouch_builder')
            # AdbError
            except AdbError as e:
                if handle_adb_error(e):
                    def init():
                        self.adb_reconnect()
                        del_cached_property(self, '_maatouch_builder')
                elif handle_unknown_host_service(e):
                    def init():
                        self.adb_start_server()
                        self.adb_reconnect()
                        del_cached_property(self, '_maatouch_builder')
                else:
                    break
            # MaaTouchNotInstalledError: Received "Aborted" from MaaTouch
            except MaaTouchNotInstalledError as e:
                logger.error(e)

                def init():
                    self.maatouch_install()
                    del_cached_property(self, '_maatouch_builder')
            except BrokenPipeError as e:
                logger.error(e)

                def init():
                    del_cached_property(self, '_maatouch_builder')
            # Unknown, probably a trucked image
            except Exception as e:
                logger.exception(e)

                def init():
                    pass

        logger.critical(f'Retry {func.__name__}() failed')
        raise RequestHumanTakeover

    return retry_wrapper


class MaatouchBuilder(CommandBuilder):
    def __init__(
            self,
            device,
            contact=0,
            handle_orientation=False,
    ):
        """
        Args:
            device (MaaTouch):
        """

        super().__init__(device, contact, handle_orientation)

    def send(self):
        return self.device.maatouch_send(builder=self)

    def send_sync(self, mode=2):
        return self.device.maatouch_send_sync(builder=self, mode=mode)

    def end(self):
        self.device.sleep(self.DEFAULT_DELAY)


class MaaTouchNotInstalledError(Exception):
    pass


class MaaTouchSyncTimeout(Exception):
    pass


class MaaTouch(Connection):
    """
    Control method that implements the same as scrcpy and has an interface similar to minitouch.
    https://github.com/MaaAssistantArknights/MaaTouch
    """
    max_x: int
    max_y: int
    _maatouch_stream: socket.socket = None
    _maatouch_stream_storage = None
    _maatouch_init_thread = None
    _maatouch_orientation: int = None

    @cached_property
    @retry
    def _maatouch_builder(self):
        self.maatouch_init()
        return MaatouchBuilder(self)

    @property
    def maatouch_builder(self):
        # Wait init thread
        if self._maatouch_init_thread is not None:
            self._maatouch_init_thread.join()
            del self._maatouch_init_thread
            self._maatouch_init_thread = None

        # Return an empty builder
        self._maatouch_builder.clear()
        return self._maatouch_builder

    def early_maatouch_init(self):
        """
        Start a thread to init maatouch connection while the Alas instance just starting to take screenshots
        This would speed up the first click 0.2 ~ 0.4s.
        """
        if has_cached_property(self, '_maatouch_builder'):
            return

        def early_maatouch_init_func():
            _ = self._maatouch_builder

        thread = threading.Thread(target=early_maatouch_init_func, daemon=True)
        self._maatouch_init_thread = thread
        thread.start()

    def on_orientation_change_maatouch(self):
        """
        MaaTouch caches devices orientation at its startup
        A restart is required when orientation changed
        """
        if self._maatouch_orientation is None:
            return
        if self.orientation == self._maatouch_orientation:
            return

        logger.info(f'Orientation changed {self._maatouch_orientation} => {self.orientation}, re-init MaaTouch')
        del_cached_property(self, '_maatouch_builder')
        self.early_maatouch_init()

    def maatouch_init(self):
        logger.hr('MaaTouch init')
        max_x, max_y = 1280, 720
        max_contacts = 2
        max_pressure = 50

        # Try to close existing stream
        if self._maatouch_stream is not None:
            try:
                self._maatouch_stream.close()
            except Exception as e:
                logger.error(e)
            del self._maatouch_stream
        if self._maatouch_stream_storage is not None:
            del self._maatouch_stream_storage

        # MaaTouch caches devices orientation at its startup
        super(MaaTouch, self).get_orientation()
        self._maatouch_orientation = self.orientation

        # CLASSPATH=/data/local/tmp/maatouch app_process / com.shxyke.MaaTouch.App
        stream = self.adb_shell(
            [f'CLASSPATH={self.config.MAATOUCH_FILEPATH_REMOTE}', 'app_process', '/', 'com.shxyke.MaaTouch.App'],
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

        # Timeout 2s for sync
        stream.settimeout(2)
        logger.info(
            "MaaTouch stream connected"
        )
        logger.info(
            "max_contact: {}; max_x: {}; max_y: {}; max_pressure: {}".format(
                max_contacts, max_x, max_y, max_pressure
            )
        )

    def maatouch_send(self, builder: MaatouchBuilder):
        content = builder.to_minitouch()
        # logger.info("send operation: {}".format(content.replace("\n", "\\n")))
        byte_content = content.encode('utf-8')
        self._maatouch_stream.sendall(byte_content)
        self._maatouch_stream.recv(0)
        self.sleep(builder.delay / 1000 + builder.DEFAULT_DELAY)
        builder.clear()

    def maatouch_send_sync(self, builder: MaatouchBuilder, mode=2):
        # Set inject mode to the last command
        for command in builder.commands[::-1]:
            if command.operation in ['r', 'd', 'm', 'u']:
                command.mode = mode
                break

        # add maatouch sync command: 's <timestamp>\n'
        timestamp = str(int(time.time() * 1000))
        builder.commands.insert(0, Command(
            's', text=timestamp
        ))

        # Send
        content = builder.to_maatouch_sync()
        # logger.info("send operation: {}".format(content.replace("\n", "\\n")))
        byte_content = content.encode('utf-8')
        self._maatouch_stream.sendall(byte_content)
        self._maatouch_stream.recv(0)

        # Wait until operations finished
        # start = time.time()
        socket_out = self._maatouch_stream.makefile()
        max_trial = 3
        for n in range(3):
            try:
                out = socket_out.readline()
            except socket.timeout as e:
                raise MaaTouchSyncTimeout(str(e))
            out = out.strip()
            # logger.info(out)

            if out == timestamp:
                break
            if out == 'Killed':
                raise MaaTouchNotInstalledError('MaaTouch died, probably because version incompatible')
            if n == max_trial - 1:
                raise MaaTouchSyncTimeout('Too many incorrect sync response')
            time.sleep(0.001)

        # logger.info(f'Delay: {builder.delay}')
        # logger.info(f'Waiting control {time.time() - start}')
        self.sleep(builder.DEFAULT_DELAY)
        builder.clear()

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
        builder.send_sync()

    @retry
    def long_click_maatouch(self, x, y, duration=1.0):
        duration = int(duration * 1000)
        builder = self.maatouch_builder
        builder.down(x, y).wait(duration).commit()
        builder.up().commit()
        builder.send_sync()

    @retry
    def swipe_maatouch(self, p1, p2):
        points = insert_swipe(p0=p1, p3=p2)
        builder = self.maatouch_builder

        builder.down(*points[0]).commit().wait(10)
        builder.send_sync()

        for point in points[1:]:
            builder.move(*point).wait(10)
        builder.commit()
        builder.send_sync()

        builder.up().commit()
        builder.send_sync()

    @retry
    def drag_maatouch(self, p1, p2, point_random=(-10, -10, 10, 10)):
        p1 = np.array(p1) - random_rectangle_point(point_random)
        p2 = np.array(p2) - random_rectangle_point(point_random)
        points = insert_swipe(p0=p1, p3=p2, speed=20)
        builder = self.maatouch_builder

        builder.down(*points[0]).commit().wait(10)
        builder.send_sync()

        for point in points[1:]:
            builder.move(*point).commit().wait(10)
        builder.send_sync()

        builder.move(*p2).commit().wait(140)
        builder.move(*p2).commit().wait(140)
        builder.send_sync()

        builder.up().commit()
        builder.send_sync()

    @retry
    def reset_maatouch(self):
        builder = self.maatouch_builder
        builder.reset().commit()
        builder.send_sync()
