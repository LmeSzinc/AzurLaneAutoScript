import time

from retrying import retry

from module.base.timer import Timer
from module.base.utils import *
from module.device.connection import Connection
from module.logger import logger


class Control(Connection):
    @staticmethod
    def sleep(second):
        """
        Args:
            second(int, float, tuple):
        """
        time.sleep(ensure_time(second))

    @property
    def time(self):
        return time.time()

    @staticmethod
    def _point2str(x, y):
        return '(%s,%s)' % (str(int(x)).rjust(4), str(int(y)).rjust(4))

    def click(self, button, adb=False):
        """Method to click a button.

        Args:
            button (button.Button): AzurLane Button instance.
            adb (bool): If use adb.
        """
        x, y = random_rectangle_point(button.button)
        logger.info(
            'Click %s @ %s' % (self._point2str(x, y), button)
        )
        if adb:
            self._click_adb(x, y)
        else:
            self._click_uiautomator2(x, y)
        self.sleep(self.config.SLEEP_AFTER_CLICK)

    @retry()
    def _click_uiautomator2(self, x, y):
        self.device.click(x, y)

    @retry()
    def _click_adb(self, x, y):
        self.adb_shell(['input', 'tap', str(x), str(y)], serial=self.serial)

    def multi_click(self, button, n, interval=(0.1, 0.2), adb=False):
        click_timer = Timer(0.1)
        for _ in range(n):
            remain = ensure_time(interval) - click_timer.current()
            if remain > 0:
                self.sleep(remain)

            click_timer.reset()
            self.click(button, adb=adb)

    def long_click(self, button, duration=(1, 1.2)):
        """Method to long click a button.

        Args:
            button (button.Button): AzurLane Button instance.
            duration(int, float, tuple):
        """
        x, y = random_rectangle_point(button.button)
        duration = ensure_time(duration)
        logger.info(
            'Click %s @ %s, %s' % (self._point2str(x, y), button, duration)
        )
        self.device.long_click(x, y, duration=duration)

    def swipe(self, vector, box=(123, 159, 1193, 628), random_range=(0, 0, 0, 0), padding=15, duration=(0.1, 0.2)):
        """Method to swipe.

        Args:
            box(tuple): Swipe in box (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
            vector(tuple): (x, y).
            random_range(tuple): (x_min, y_min, x_max, y_max).
            padding(int):
            duration(int, float, tuple):
        """
        duration = ensure_time(duration)
        vector = np.array(vector) + random_rectangle_point(random_range)
        vector = np.round(vector).astype(np.int)
        half_vector = np.round(vector / 2).astype(np.int)
        box = np.array(box) + np.append(np.abs(half_vector) + padding, -np.abs(half_vector) - padding)
        center = random_rectangle_point(box)
        start_point = center - half_vector
        end_point = start_point + vector
        logger.info(
            'Swipe %s -> %s, %s' % (self._point2str(*start_point), self._point2str(*end_point), duration)
        )
        fx, fy, tx, ty = np.append(start_point, end_point).tolist()
        if fx < 0 or tx < 0:
            logger.warning('Swipe Error. vector: %s, box: %s, center: %s, half_vector: %s' % (
                str(vector), str(box), str(center), str(half_vector)
            ))
        self.device.swipe(fx, fy, tx, ty, duration=duration)

    def drag(self, path):
        """Swipe following path.

        Args:
            path (list): (x, y, sleep)

        Examples:
            al.swipe([
                (403, 421, 0.2),
                (821, 326, 0.1),
                (821, 326-10, 0.1),
                (821, 326+10, 0.1),
                (821, 326, 0),
            ])
            Equals to:
            al.device.touch.down(403, 421)
            time.sleep(0.2)
            al.device.touch.move(821, 326)
            time.sleep(0.1)
            al.device.touch.move(821, 326-10)
            time.sleep(0.1)
            al.device.touch.move(821, 326+10)
            time.sleep(0.1)
            al.device.touch.up(821, 326)
        """
        length = len(path)
        for index, data in enumerate(path):
            x, y, second = data
            if index == 0:
                self.device.touch.down(x, y)
                logger.info(self._point2str(x, y) + ' down')
            elif index - length == -1:
                self.device.touch.up(x, y)
                logger.info(self._point2str(x, y) + ' up')
            else:
                self.device.touch.move(x, y)
                logger.info(self._point2str(x, y) + ' move')
            self.sleep(second)

    def drag_node(self, location, offset=(-10, -10, 10, 10), sleep=0.25, reverse=False):
        """Generate a swipe node.

        Args:
            location (tuple): Origin location (x, y).
            offset (tuple): set
            sleep:
            reverse (bool): Reverse offset. Default to false.

        Returns:
            tuple: (x, y, sleep)
        """
        if not reverse:
            location = np.array(location) - random_rectangle_point(offset)
        else:
            location = np.array(location) + random_rectangle_point(offset)
        location = tuple(np.append(location, [sleep]))
        return location
