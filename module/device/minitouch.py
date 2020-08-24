import random
import socket
import time

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
    for t in ts:
        point = p0 * (1 - t) ** 3 + 3 * p1 * t * (1 - t) ** 2 + 3 * p2 * t ** 2 * (1 - t) + p3 * t ** 3
        points.append(point.astype(np.int).tolist())

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

    def __init__(self):
        self.content = ""
        self.delay = 0

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
        self.append("d {} {} {} {}".format(contact_id, x, y, pressure))
        return self

    def move(self, x, y, contact_id=0, pressure=100):
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

    def minitouch_init(self):
        logger.hr('MiniTouch init')

        self._minitouch_port = get_port()
        logger.info(f"Minitouch bind to port {self._minitouch_port}")

        self.adb_forward([f"tcp:{self._minitouch_port}", "localabstract:minitouch"], serial=self.serial)
        logger.info(f"Minitouch forward port {self._minitouch_port}")

        # No need, minitouch already started by uiautomator2
        # self.adb_shell([self.config.MINITOUCH_FILEPATH_REMOTE], serial=self.serial)

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
        # self.max_x = max_x
        # self.max_y = max_y
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

    def _minitouch_send(self, builder):
        """
        Args:
            builder (CommandBuilder):
        """
        if not self._minitouch_has_init:
            self.minitouch_init()

        content = builder.content
        # logger.info("send operation: {}".format(content.replace("\n", "\\n")))
        byte_content = content.encode('utf-8')
        self.client.sendall(byte_content)
        self.client.recv(0)
        time.sleep(builder.delay / 1000 + builder.DEFAULT_DELAY)
        builder.reset()

    def _click_minitouch(self, x, y):
        builder = CommandBuilder()
        builder.down(x, y).commit()
        builder.up().commit()
        self._minitouch_send(builder)

    def _swipe_minitouch(self, fx, fy, tx, ty):
        points = insert_swipe(p0=(fx, fy), p3=(tx, ty))
        builder = CommandBuilder()

        builder.down(*points[0]).commit()
        self._minitouch_send(builder)

        for point in points[1:]:
            builder.move(*point).commit().wait(10)
        self._minitouch_send(builder)

        builder.up().commit()
        self._minitouch_send(builder)

    def _drag_minitouch(self, p1, p2, point_random=(-10, -10, 10, 10)):
        p1 = np.array(p1) - random_rectangle_point(point_random)
        p2 = np.array(p2) - random_rectangle_point(point_random)
        points = insert_swipe(p0=p1, p3=p2, speed=20)
        builder = CommandBuilder()

        builder.down(*points[0]).commit()
        self._minitouch_send(builder)

        for point in points[1:]:
            builder.move(*point).commit().wait(10)
        self._minitouch_send(builder)

        builder.move(*p2).commit().wait(140)
        builder.move(*p2).commit().wait(140)
        self._minitouch_send(builder)

        builder.up().commit()
        self._minitouch_send(builder)
