import asyncio
import json
import socket
import threading
import time
from functools import wraps
from typing import List

import websockets
from adbutils.errors import AdbError
from uiautomator2 import _Service

from module.base.decorator import Config, cached_property, del_cached_property, has_cached_property
from module.base.timer import Timer
from module.base.utils import *
from module.device.connection import Connection
from module.device.method.utils import RETRY_TRIES, handle_adb_error, handle_unknown_host_service, retry_sleep
from module.exception import RequestHumanTakeover, ScriptError
from module.logger import logger


def random_normal_distribution(a, b, n=5):
    output = np.mean(np.random.uniform(a, b, size=n))
    return output


def random_theta():
    theta = np.random.uniform(0, 2 * np.pi)
    return np.array([np.sin(theta), np.cos(theta)])


def random_rho(dis):
    return random_normal_distribution(-dis, dis)


def insert_swipe(p0, p3, speed=15, min_distance=10):
    """
    Insert way point from start to end.
    First generate a cubic bézier curve

    Args:
        p0: Start point.
        p3: End point.
        speed: Average move speed, pixels per 10ms.
        min_distance:

    Returns:
        list[list[int]]: List of points.

    Examples:
        > insert_swipe((400, 400), (600, 600), speed=20)
        [[400, 400], [406, 406], [416, 415], [429, 428], [444, 442], [462, 459], [481, 478], [504, 500], [527, 522],
        [545, 540], [560, 557], [573, 570], [584, 582], [592, 590], [597, 596], [600, 600]]
    """
    p0 = np.array(p0)
    p3 = np.array(p3)

    # Random control points in Bézier curve
    distance = np.linalg.norm(p3 - p0)
    p1 = 2 / 3 * p0 + 1 / 3 * p3 + random_theta() * random_rho(distance * 0.1)
    p2 = 1 / 3 * p0 + 2 / 3 * p3 + random_theta() * random_rho(distance * 0.1)

    # Random `t` on Bézier curve, sparse in the middle, dense at start and end
    segments = max(int(distance / speed) + 1, 5)
    lower = random_normal_distribution(-85, -60)
    upper = random_normal_distribution(80, 90)
    theta = np.arange(lower + 0., upper + 0.0001, (upper - lower) / segments)
    ts = np.sin(theta / 180 * np.pi)
    ts = np.sign(ts) * abs(ts) ** 0.9
    ts = (ts - min(ts)) / (max(ts) - min(ts))

    # Generate cubic Bézier curve
    points = []
    prev = (-100, -100)
    for t in ts:
        point = p0 * (1 - t) ** 3 + 3 * p1 * t * (1 - t) ** 2 + 3 * p2 * t ** 2 * (1 - t) + p3 * t ** 3
        point = point.astype(int).tolist()
        if np.linalg.norm(np.subtract(point, prev)) < min_distance:
            continue

        points.append(point)
        prev = point

    # Delete nearing points
    if len(points[1:]):
        distance = np.linalg.norm(np.subtract(points[1:], points[0]), axis=1)
        mask = np.append(True, distance > min_distance)
        points = np.array(points)[mask].tolist()
        if len(points) <= 1:
            points = [p0, p3]
    else:
        points = [p0, p3]

    return points


class Command:
    def __init__(
            self,
            operation: str,
            contact: int = 0,
            x: int = 0,
            y: int = 0,
            ms: int = 10,
            pressure: int = 100,
            mode: int = 0,
            text: str = ''
    ):
        """
        See https://github.com/openstf/minitouch#writable-to-the-socket

        Args:
            operation: c, r, d, m, u, w
            contact:
            x:
            y:
            ms:
            pressure:
            mode:
            text:
        """
        self.operation = operation
        self.contact = contact
        self.x = x
        self.y = y
        self.ms = ms
        self.pressure = pressure
        self.mode = mode
        self.text = text

    def to_minitouch(self) -> str:
        """
        String that write into minitouch socket
        """
        if self.operation == 'c':
            return f'{self.operation}\n'
        elif self.operation == 'r':
            return f'{self.operation}\n'
        elif self.operation == 'd':
            return f'{self.operation} {self.contact} {self.x} {self.y} {self.pressure}\n'
        elif self.operation == 'm':
            return f'{self.operation} {self.contact} {self.x} {self.y} {self.pressure}\n'
        elif self.operation == 'u':
            return f'{self.operation} {self.contact}\n'
        elif self.operation == 'w':
            return f'{self.operation} {self.ms}\n'
        else:
            return ''

    def to_maatouch_sync(self):
        if self.operation == 'c':
            return f'{self.operation}\n'
        elif self.operation == 'r':
            if self.mode:
                return f'{self.operation} {self.mode}\n'
            else:
                return f'{self.operation}\n'
        elif self.operation == 'd':
            if self.mode:
                return f'{self.operation} {self.contact} {self.x} {self.y} {self.pressure} {self.mode}\n'
            else:
                return f'{self.operation} {self.contact} {self.x} {self.y} {self.pressure}\n'
        elif self.operation == 'm':
            if self.mode:
                return f'{self.operation} {self.contact} {self.x} {self.y} {self.pressure} {self.mode}\n'
            else:
                return f'{self.operation} {self.contact} {self.x} {self.y} {self.pressure}\n'
        elif self.operation == 'u':
            if self.mode:
                return f'{self.operation} {self.contact} {self.mode}\n'
            else:
                return f'{self.operation} {self.ms}\n'
        elif self.operation == 'w':
            return f'{self.operation} {self.ms}\n'
        elif self.operation == 's':
            return f'{self.operation} {self.text}\n'
        else:
            return ''

    def to_atx_agent(self, max_x=1280, max_y=720) -> str:
        """
        Dict that send to atx-agent, $DEVICE_URL/minitouch
        See https://github.com/openatx/atx-agent#minitouch%E6%93%8D%E4%BD%9C%E6%96%B9%E6%B3%95
        """
        x, y = self.x / max_x, self.y / max_y
        if self.operation == 'c':
            out = dict(operation=self.operation)
        elif self.operation == 'r':
            out = dict(operation=self.operation)
        elif self.operation == 'd':
            out = dict(operation=self.operation, index=self.contact, pressure=self.pressure, xP=x, yP=y)
        elif self.operation == 'm':
            out = dict(operation=self.operation, index=self.contact, pressure=self.pressure, xP=x, yP=y)
        elif self.operation == 'u':
            out = dict(operation=self.operation, index=self.contact)
        elif self.operation == 'w':
            out = dict(operation=self.operation, milliseconds=self.ms)
        else:
            out = dict()
        return json.dumps(out)


class CommandBuilder:
    """Build command str for minitouch.

    You can use this, to custom actions as you wish::

        with safe_connection(_DEVICE_ID) as connection:
            builder = CommandBuilder()
            builder.down(0, 400, 400, 50)
            builder.commit()
            builder.move(0, 500, 500, 50)
            builder.commit()
            builder.move(0, 800, 400, 50)
            builder.commit()
            builder.up(0)
            builder.commit()
            builder.publish(connection)

    """
    DEFAULT_DELAY = 0.05
    max_x = 1280
    max_y = 720

    def __init__(
            self,
            device,
            contact=0,
            handle_orientation=True,
    ):
        """
        Args:
            device:
        """
        self.device = device
        self.commands = []
        self.delay = 0
        self.contact = contact
        self.handle_orientation = handle_orientation

    @property
    def orientation(self):
        if self.handle_orientation:
            return self.device.orientation
        else:
            return 0

    def convert(self, x, y):
        max_x, max_y = self.device.max_x, self.device.max_y
        orientation = self.orientation

        if orientation == 0:
            pass
        elif orientation == 1:
            x, y = 720 - y, x
            max_x, max_y = max_y, max_x
        elif orientation == 2:
            x, y = 1280 - x, 720 - y
        elif orientation == 3:
            x, y = y, 1280 - x
            max_x, max_y = max_y, max_x
        else:
            raise ScriptError(f'Invalid device orientation: {orientation}')

        self.max_x, self.max_y = max_x, max_y
        if not self.device.config.DEVICE_OVER_HTTP:
            # Maximum X and Y coordinates may, but usually do not, match the display size.
            x, y = int(x / 1280 * max_x), int(y / 720 * max_y)
        else:
            # When over http, max_x and max_y are default to 1280 and 720, skip matching display size
            x, y = int(x), int(y)
        return x, y

    def commit(self):
        """ add minitouch command: 'c\n' """
        self.commands.append(Command(
            'c'
        ))
        return self

    def reset(self, mode=0):
        """ add minitouch command: 'r\n' """
        self.commands.append(Command(
            'r', mode=mode
        ))
        return self

    def wait(self, ms=10):
        """ add minitouch command: 'w <ms>\n' """
        self.commands.append(Command(
            'w', ms=ms
        ))
        self.delay += ms
        return self

    def up(self, mode=0):
        """ add minitouch command: 'u <contact>\n' """
        self.commands.append(Command(
            'u', contact=self.contact, mode=mode
        ))
        return self

    def down(self, x, y, pressure=100, mode=0):
        """ add minitouch command: 'd <contact> <x> <y> <pressure>\n' """
        x, y = self.convert(x, y)
        self.commands.append(Command(
            'd', x=x, y=y, contact=self.contact, pressure=pressure, mode=mode
        ))
        return self

    def move(self, x, y, pressure=100, mode=0):
        """ add minitouch command: 'm <contact> <x> <y> <pressure>\n' """
        x, y = self.convert(x, y)
        self.commands.append(Command(
            'm', x=x, y=y, contact=self.contact, pressure=pressure, mode=mode
        ))
        return self

    def clear(self):
        """ clear current commands """
        self.commands = []
        self.delay = 0
        return self

    def to_minitouch(self) -> str:
        out = ''.join([command.to_minitouch() for command in self.commands])
        self._check_empty(out)
        return out

    def to_maatouch_sync(self) -> str:
        out = ''.join([command.to_maatouch_sync() for command in self.commands])
        self._check_empty(out)
        return out

    def to_atx_agent(self) -> List[str]:
        out = [command.to_atx_agent(self.max_x, self.max_y) for command in self.commands]
        self._check_empty(out)
        return out

    def send(self):
        return self.device.minitouch_send(builder=self)

    def _check_empty(self, text=None):
        """
        A valid command list must includes some operations not just committing

        Returns:
            bool: If command is empty
        """
        empty = True
        for command in self.commands:
            if command.operation not in ['c', 'w', 's']:
                empty = False
                break
        if empty:
            logger.warning(f'Command list empty, sending it may cause unexpected behaviour: {text}')
        return empty


class MinitouchNotInstalledError(Exception):
    pass


class MinitouchOccupiedError(Exception):
    pass


class U2Service(_Service):
    def __init__(self, name, u2obj):
        self.name = name
        self.u2obj = u2obj
        self.service_url = self.u2obj.path2url("/services/" + name)


def retry(func):
    @wraps(func)
    def retry_wrapper(self, *args, **kwargs):
        """
        Args:
            self (Minitouch):
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
                    if self._minitouch_port:
                        self.adb_forward_remove(f'tcp:{self._minitouch_port}')
                    del_cached_property(self, '_minitouch_builder')
            # Emulator closed
            except ConnectionAbortedError as e:
                logger.error(e)

                def init():
                    self.adb_reconnect()
                    if self._minitouch_port:
                        self.adb_forward_remove(f'tcp:{self._minitouch_port}')
                    del_cached_property(self, '_minitouch_builder')
            # MinitouchNotInstalledError: Received empty data from minitouch
            except MinitouchNotInstalledError as e:
                logger.error(e)

                def init():
                    self.install_uiautomator2()
                    if self._minitouch_port:
                        self.adb_forward_remove(f'tcp:{self._minitouch_port}')
                    del_cached_property(self, '_minitouch_builder')
            # MinitouchOccupiedError: Timeout when connecting to minitouch
            except MinitouchOccupiedError as e:
                logger.error(e)

                def init():
                    self.restart_atx()
                    if self._minitouch_port:
                        self.adb_forward_remove(f'tcp:{self._minitouch_port}')
                    del_cached_property(self, '_minitouch_builder')
            # AdbError
            except AdbError as e:
                if handle_adb_error(e):
                    def init():
                        self.adb_reconnect()
                        if self._minitouch_port:
                            self.adb_forward_remove(f'tcp:{self._minitouch_port}')
                        del_cached_property(self, '_minitouch_builder')
                elif handle_unknown_host_service(e):
                    def init():
                        self.adb_start_server()
                        self.adb_reconnect()
                        if self._minitouch_port:
                            self.adb_forward_remove(f'tcp:{self._minitouch_port}')
                        del_cached_property(self, '_minitouch_builder')
                else:
                    break
            except BrokenPipeError as e:
                logger.error(e)

                def init():
                    del_cached_property(self, '_minitouch_builder')
            # Unknown, probably a trucked image
            except Exception as e:
                logger.exception(e)

                def init():
                    pass

        logger.critical(f'Retry {func.__name__}() failed')
        raise RequestHumanTakeover

    return retry_wrapper


class Minitouch(Connection):
    _minitouch_port: int = 0
    _minitouch_client: socket.socket = None
    _minitouch_pid: int
    _minitouch_ws: websockets.WebSocketClientProtocol
    max_x: int
    max_y: int
    _minitouch_init_thread = None

    @cached_property
    @retry
    def _minitouch_builder(self):
        self.minitouch_init()
        return CommandBuilder(self)

    @property
    def minitouch_builder(self):
        # Wait init thread
        if self._minitouch_init_thread is not None:
            self._minitouch_init_thread.join()
            del self._minitouch_init_thread
            self._minitouch_init_thread = None

        return self._minitouch_builder

    def early_minitouch_init(self):
        """
        Start a thread to init minitouch connection while the Alas instance just starting to take screenshots
        This would speed up the first click 0.05s.
        """
        if has_cached_property(self, '_minitouch_builder'):
            return

        def early_minitouch_init_func():
            _ = self._minitouch_builder

        thread = threading.Thread(target=early_minitouch_init_func, daemon=True)
        self._minitouch_init_thread = thread
        thread.start()

    @Config.when(DEVICE_OVER_HTTP=False)
    def minitouch_init(self):
        logger.hr('MiniTouch init')
        max_x, max_y = 1280, 720
        max_contacts = 2
        max_pressure = 50

        # Try to close existing stream
        if self._minitouch_client is not None:
            try:
                self._minitouch_client.close()
            except Exception as e:
                logger.error(e)
            del self._minitouch_client

        self.get_orientation()

        self._minitouch_port = self.adb_forward("localabstract:minitouch")

        # No need, minitouch already started by uiautomator2
        # self.adb_shell([self.config.MINITOUCH_FILEPATH_REMOTE])

        retry_timeout = Timer(2).start()
        while 1:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(1)
            client.connect(('127.0.0.1', self._minitouch_port))
            self._minitouch_client = client

            # get minitouch server info
            socket_out = client.makefile()

            # v <version>
            # protocol version, usually it is 1. needn't use this
            try:
                out = socket_out.readline().replace("\n", "").replace("\r", "")
            except socket.timeout:
                client.close()
                raise MinitouchOccupiedError(
                    'Timeout when connecting to minitouch, '
                    'probably because another connection has been established'
                )
            logger.info(out)

            # ^ <max-contacts> <max-x> <max-y> <max-pressure>
            out = socket_out.readline().replace("\n", "").replace("\r", "")
            logger.info(out)
            try:
                _, max_contacts, max_x, max_y, max_pressure, *_ = out.split(" ")
                break
            except ValueError:
                client.close()
                if retry_timeout.reached():
                    raise MinitouchNotInstalledError(
                        'Received empty data from minitouch, '
                        'probably because minitouch is not installed'
                    )
                else:
                    # Minitouch may not start that fast
                    self.sleep(1)
                    continue

        # self.max_contacts = max_contacts
        self.max_x = int(max_x)
        self.max_y = int(max_y)
        # self.max_pressure = max_pressure

        # $ <pid>
        out = socket_out.readline().replace("\n", "").replace("\r", "")
        logger.info(out)
        _, pid = out.split(" ")
        self._minitouch_pid = pid

        logger.info(
            "minitouch running on port: {}, pid: {}".format(self._minitouch_port, self._minitouch_pid)
        )
        logger.info(
            "max_contact: {}; max_x: {}; max_y: {}; max_pressure: {}".format(
                max_contacts, max_x, max_y, max_pressure
            )
        )

    @Config.when(DEVICE_OVER_HTTP=False)
    def minitouch_send(self, builder: CommandBuilder):
        content = builder.to_minitouch()
        # logger.info("send operation: {}".format(content.replace("\n", "\\n")))
        byte_content = content.encode('utf-8')
        self._minitouch_client.sendall(byte_content)
        self._minitouch_client.recv(0)
        time.sleep(self.minitouch_builder.delay / 1000 + builder.DEFAULT_DELAY)
        builder.clear()

    @cached_property
    def _minitouch_loop(self):
        return asyncio.new_event_loop()

    def _minitouch_loop_run(self, event):
        """
        Args:
            event: Async function

        Raises:
            MinitouchOccupiedError
        """
        try:
            return self._minitouch_loop.run_until_complete(event)
        except websockets.ConnectionClosedError as e:
            # ConnectionClosedError: no close frame received or sent
            # ConnectionClosedError: sent 1011 (unexpected error) keepalive ping timeout; no close frame received
            logger.error(e)
            raise MinitouchOccupiedError(
                'ConnectionClosedError, '
                'probably because another connection has been established'
            )

    @Config.when(DEVICE_OVER_HTTP=True)
    def minitouch_init(self):
        logger.hr('MiniTouch init')
        self.max_x, self.max_y = 1280, 720
        self.get_orientation()

        logger.info('Stop minitouch service')
        s = U2Service('minitouch', self.u2)
        s.stop()
        while 1:
            if not s.running():
                break
            self.sleep(0.05)

        logger.info('Start minitouch service')
        s.start()
        while 1:
            if s.running():
                break
            self.sleep(0.05)

        # 'ws://127.0.0.1:7912/minitouch'
        url = re.sub(r"^https?://", 'ws://', self.serial) + '/minitouch'
        logger.attr('Minitouch', url)

        async def connect():
            ws = await websockets.connect(url)
            # start @minitouch service
            logger.info(await ws.recv())
            # dial unix:@minitouch
            logger.info(await ws.recv())
            return ws

        self._minitouch_ws = self._minitouch_loop_run(connect())

    @Config.when(DEVICE_OVER_HTTP=True)
    def minitouch_send(self, builder: CommandBuilder):
        content = builder.to_atx_agent()

        async def send():
            for row in content:
                # logger.info("send operation: {}".format(row.replace("\n", "\\n")))
                await self._minitouch_ws.send(row)

        self._minitouch_loop_run(send())
        time.sleep(builder.delay / 1000 + builder.DEFAULT_DELAY)
        builder.clear()

    @retry
    def click_minitouch(self, x, y):
        builder = self.minitouch_builder
        builder.down(x, y).commit()
        builder.up().commit()
        builder.send()

    @retry
    def long_click_minitouch(self, x, y, duration=1.0):
        duration = int(duration * 1000)
        builder = self.minitouch_builder
        builder.down(x, y).commit().wait(duration)
        builder.up().commit()
        builder.send()

    @retry
    def swipe_minitouch(self, p1, p2):
        points = insert_swipe(p0=p1, p3=p2)
        builder = self.minitouch_builder

        builder.down(*points[0]).commit()
        builder.send()

        for point in points[1:]:
            builder.move(*point).commit().wait(10)
        builder.send()

        builder.up().commit()
        builder.send()

    @retry
    def drag_minitouch(self, p1, p2, point_random=(-10, -10, 10, 10)):
        p1 = np.array(p1) - random_rectangle_point(point_random)
        p2 = np.array(p2) - random_rectangle_point(point_random)
        points = insert_swipe(p0=p1, p3=p2, speed=20)
        builder = self.minitouch_builder

        builder.down(*points[0]).commit()
        builder.send()

        for point in points[1:]:
            builder.move(*point).commit().wait(10)
        builder.send()

        builder.move(*p2).commit().wait(140)
        builder.move(*p2).commit().wait(140)
        builder.send()

        builder.up().commit()
        builder.send()
