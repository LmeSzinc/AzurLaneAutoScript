import socket
import time
from functools import wraps

from adbutils.errors import AdbError

from module.base.decorator import cached_property
from module.base.timer import Timer
from module.base.utils import *
from module.device.connection import Connection
from module.device.method.utils import (RETRY_DELAY, RETRY_TRIES,
                                        del_cached_property, handle_adb_error)
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


def insert_swipe(p0, p3, speed=15):
    """
    Insert way point from start to end.
    First generate a cubic bézier curve

    Args:
        p0: Start point.
        p3: End point.
        speed: Average move speed, pixels per 10ms.

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
        point = point.astype(np.int).tolist()
        if np.linalg.norm(np.subtract(point, prev)) < 10:
            continue

        points.append(point)
        prev = point

    # Delete nearing points
    if len(points[1:]):
        distance = np.linalg.norm(np.subtract(points[1:], points[0]), axis=1)
        mask = np.append(True, distance > 10)
        points = np.array(points)[mask].tolist()
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
            pressure: int = 100
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
        """
        self.operation = operation
        self.contact = contact
        self.x = x
        self.y = y
        self.ms = ms
        self.pressure = pressure

    def to_minitouch_string(self):
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

    def to_atx_agent_dict(self):
        """
        Dict that send to atx-agent, $DEVICE_URL/minitouch
        See https://github.com/openatx/atx-agent#minitouch%E6%93%8D%E4%BD%9C%E6%96%B9%E6%B3%95
        """
        if self.operation == 'c':
            return dict(operation=self.operation)
        elif self.operation == 'r':
            return dict(operation=self.operation)
        elif self.operation == 'd':
            return dict(operation=self.operation, index=self.contact, xP=self.x, yP=self.y, pressure=self.pressure)
        elif self.operation == 'm':
            return dict(operation=self.operation, index=self.contact, xP=self.x, yP=self.y, pressure=self.pressure)
        elif self.operation == 'u':
            return dict(operation=self.operation, index=self.contact)
        elif self.operation == 'w':
            return dict(operation=self.operation, milliseconds=self.ms)
        else:
            return dict()


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

    def __init__(self, device):
        """
        Args:
            device (Minitouch):
        """
        self.device = device
        self.commands = []
        self.delay = 0

    def convert(self, x, y):
        max_x, max_y = self.device.max_x, self.device.max_y
        orientation = self.device.orientation

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

        # Maximum X and Y coordinates may, but usually do not, match the display size.
        x, y = int(x / 1280 * max_x), int(y / 720 * max_y)
        return x, y

    def commit(self):
        """ add minitouch command: 'c\n' """
        self.commands.append(Command('c'))
        return self

    def wait(self, ms=10):
        """ add minitouch command: 'w <ms>\n' """
        self.commands.append(Command('w', ms=ms))
        self.delay += ms
        return self

    def up(self, contact=0):
        """ add minitouch command: 'u <contact>\n' """
        self.commands.append(Command('u', contact=contact))
        return self

    def down(self, x, y, contact=0, pressure=100):
        """ add minitouch command: 'd <contact> <x> <y> <pressure>\n' """
        x, y = self.convert(x, y)
        self.commands.append(Command('d', x=x, y=y, contact=contact, pressure=pressure))
        return self

    def move(self, x, y, contact=0, pressure=100):
        """ add minitouch command: 'm <contact> <x> <y> <pressure>\n' """
        x, y = self.convert(x, y)
        self.commands.append(Command('m', x=x, y=y, contact=contact, pressure=pressure))
        return self

    def reset(self):
        """ clear current commands """
        self.commands = []
        self.delay = 0

    def to_minitouch_string(self):
        return ''.join([command.to_minitouch_string() for command in self.commands])

    def to_atx_agent_dict(self):
        return [command.to_atx_agent_dict() for command in self.commands]


class MinitouchNotInstalledError(Exception):
    pass


class MinitouchOccupiedError(Exception):
    pass


def retry(func):
    @wraps(func)
    def retry_wrapper(self, *args, **kwargs):
        """
        Args:
            self (Minitouch):
        """
        init = None
        sleep = True
        for _ in range(RETRY_TRIES):
            try:
                if callable(init):
                    if sleep:
                        self.sleep(RETRY_DELAY)
                        sleep = True
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
            # Emulator closed
            except ConnectionAbortedError as e:
                logger.error(e)

                def init():
                    self.adb_reconnect()
            # MinitouchNotInstalledError: Received empty data from minitouch
            except MinitouchNotInstalledError as e:
                logger.error(e)
                sleep = False

                def init():
                    self.install_uiautomator2()
                    if self._minitouch_port:
                        self.adb_forward_remove(f'tcp:{self._minitouch_port}')
                    del_cached_property(self, 'minitouch_builder')
            # MinitouchOccupiedError: Timeout when connecting to minitouch
            except MinitouchOccupiedError as e:
                logger.error(e)
                sleep = False

                def init():
                    self.restart_atx()
                    if self._minitouch_port:
                        self.adb_forward_remove(f'tcp:{self._minitouch_port}')
                    del_cached_property(self, 'minitouch_builder')
            # AdbError
            except AdbError as e:
                if handle_adb_error(e):
                    def init():
                        self.adb_reconnect()
                else:
                    break
            except BrokenPipeError as e:
                logger.error(e)

                def init():
                    del_cached_property(self, 'minitouch_builder')
            # Unknown, probably a trucked image
            except Exception as e:
                logger.exception(e)

                def init():
                    pass

        logger.critical(f'Retry {func.__name__}() failed')
        raise RequestHumanTakeover

    return retry_wrapper


class Minitouch(Connection):
    _minitouch_port: int
    _minitouch_client: socket.socket
    _minitouch_pid: int
    max_x: int
    max_y: int

    @cached_property
    def minitouch_builder(self):
        self.minitouch_init()
        return CommandBuilder(self)

    def minitouch_init(self):
        logger.hr('MiniTouch init')

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

    def minitouch_send(self):
        content = self.minitouch_builder.to_minitouch_string()
        # logger.info("send operation: {}".format(content.replace("\n", "\\n")))
        byte_content = content.encode('utf-8')
        self._minitouch_client.sendall(byte_content)
        self._minitouch_client.recv(0)
        time.sleep(self.minitouch_builder.delay / 1000 + self.minitouch_builder.DEFAULT_DELAY)
        self.minitouch_builder.reset()

    @retry
    def click_minitouch(self, x, y):
        builder = self.minitouch_builder
        builder.down(x, y).commit()
        builder.up().commit()
        self.minitouch_send()

    @retry
    def long_click_minitouch(self, x, y, duration=1.0):
        duration = int(duration * 1000)
        builder = self.minitouch_builder
        builder.down(x, y).commit().wait(duration)
        builder.up().commit()
        self.minitouch_send()

    @retry
    def swipe_minitouch(self, p1, p2):
        points = insert_swipe(p0=p1, p3=p2)
        builder = self.minitouch_builder

        builder.down(*points[0]).commit()
        self.minitouch_send()

        for point in points[1:]:
            builder.move(*point).commit().wait(10)
        self.minitouch_send()

        builder.up().commit()
        self.minitouch_send()

    @retry
    def drag_minitouch(self, p1, p2, point_random=(-10, -10, 10, 10)):
        p1 = np.array(p1) - random_rectangle_point(point_random)
        p2 = np.array(p2) - random_rectangle_point(point_random)
        points = insert_swipe(p0=p1, p3=p2, speed=20)
        builder = self.minitouch_builder

        builder.down(*points[0]).commit()
        self.minitouch_send()

        for point in points[1:]:
            builder.move(*point).commit().wait(10)
        self.minitouch_send()

        builder.move(*p2).commit().wait(140)
        builder.move(*p2).commit().wait(140)
        self.minitouch_send()

        builder.up().commit()
        self.minitouch_send()
