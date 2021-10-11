import random
import socket
import time

from module.base.decorator import cached_property
from module.base.utils import *
from module.device.connection import Connection
from module.logger import logger

PORT_RANGE = (20000, 21000)


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


def get_port():
    """ get a random port from port set """
    new_port = random.choice(list(range(*PORT_RANGE)))
    if is_port_using(new_port):
        return get_port()
    return new_port


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

    def __init__(self, max_x, max_y):
        self.max_x = max_x
        self.max_y = max_y
        self.content = ""
        self.delay = 0

    def convert(self, x, y):
        # Maximum X and Y coordinates may, but usually do not, match the display size.
        return int(x / 1280 * self.max_x), int(y / 720 * self.max_y)

    def append(self, new_content):
        self.content += new_content + "\n"

    def commit(self):
        """ add minitouch command: 'c\n' """
        self.append("c")
        return self

    def wait(self, ms=10):
        """ add minitouch command: 'w <ms>\n' """
        self.append("w {}".format(ms))
        self.delay += ms
        return self

    def up(self, contact_id=0):
        """ add minitouch command: 'u <contact_id>\n' """
        self.append("u {}".format(contact_id))
        return self

    def down(self, x, y, contact_id=0, pressure=100):
        """ add minitouch command: 'd <contact_id> <x> <y> <pressure>\n' """
        x, y = self.convert(x, y)
        self.append("d {} {} {} {}".format(contact_id, x, y, pressure))
        return self

    def move(self, x, y, contact_id=0, pressure=100):
        x, y = self.convert(x, y)
        """ add minitouch command: 'm <contact_id> <x> <y> <pressure>\n' """
        self.append("m {} {} {} {}".format(contact_id, x, y, pressure))
        return self

    def reset(self):
        """ clear current commands """
        self.content = ""
        self.delay = 0


class MiniTouch(Connection):
    _minitouch_port = 0
    _minitouch_process = None
    _minitouch_has_init = False
    max_x: int
    max_y: int

    @cached_property
    def minitouch_builder(self):
        if not self._minitouch_has_init:
            self.minitouch_init()

        return CommandBuilder(self.max_x, self.max_y)

    def minitouch_init(self):
        logger.hr('MiniTouch init')

        self._minitouch_port = get_port()
        logger.info(f"Minitouch bind to port {self._minitouch_port}")

        self.adb_forward([f"tcp:{self._minitouch_port}", "localabstract:minitouch"])
        logger.info(f"Minitouch forward port {self._minitouch_port}")

        # No need, minitouch already started by uiautomator2
        # self.adb_shell([self.config.MINITOUCH_FILEPATH_REMOTE])

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', self._minitouch_port))
        self.client = client

        # get minitouch server info
        socket_out = client.makefile()

        # v <version>
        # protocol version, usually it is 1. needn't use this
        socket_out.readline()

        # ^ <max-contacts> <max-x> <max-y> <max-pressure>
        _, max_contacts, max_x, max_y, max_pressure, *_ = (
            socket_out.readline().replace("\n", "").replace("\r", "").split(" ")
        )
        # self.max_contacts = max_contacts
        self.max_x = int(max_x)
        self.max_y = int(max_y)
        # self.max_pressure = max_pressure

        # $ <pid>
        _, pid = socket_out.readline().replace("\n", "").replace("\r", "").split(" ")
        self.pid = pid

        logger.info(
            "minitouch running on port: {}, pid: {}".format(self._minitouch_port, self.pid)
        )
        logger.info(
            "max_contact: {}; max_x: {}; max_y: {}; max_pressure: {}".format(
                max_contacts, max_x, max_y, max_pressure
            )
        )
        self._minitouch_has_init = True

    def minitouch_send(self):
        content = self.minitouch_builder.content
        # logger.info("send operation: {}".format(content.replace("\n", "\\n")))
        byte_content = content.encode('utf-8')
        self.client.sendall(byte_content)
        self.client.recv(0)
        time.sleep(self.minitouch_builder.delay / 1000 + self.minitouch_builder.DEFAULT_DELAY)
        self.minitouch_builder.reset()

    def _click_minitouch(self, x, y):
        builder = self.minitouch_builder
        builder.down(x, y).commit()
        builder.up().commit()
        self.minitouch_send()

    def _swipe_minitouch(self, fx, fy, tx, ty):
        points = insert_swipe(p0=(fx, fy), p3=(tx, ty))
        builder = self.minitouch_builder

        builder.down(*points[0]).commit()
        self.minitouch_send()

        for point in points[1:]:
            builder.move(*point).commit().wait(10)
        self.minitouch_send()

        builder.up().commit()
        self.minitouch_send()

    def _drag_minitouch(self, p1, p2, point_random=(-10, -10, 10, 10)):
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
