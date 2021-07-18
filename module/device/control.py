import time
from collections import deque

from retrying import retry

from module.base.timer import Timer
from module.base.utils import *
from module.device.minitouch import MiniTouch
from module.exception import GameTooManyClickError
from module.logger import logger


class Control(MiniTouch):
    click_record = deque(maxlen=15)

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

    def click_record_check(self, button):
        """
        Args:
            button (button.Button): AzurLane Button instance.

        Returns:
            bool:

        Raises:
            GameTooManyClickError:
        """
        self.click_record.append(str(button))

        count = {}
        for key in self.click_record:
            count[key] = count.get(key, 0) + 1
        count = sorted(count.items(), key=lambda item: item[1])
        if count[0][1] >= 12:
            logger.warning(f'Too many click for a button: {count[0][0]}')
            logger.info(f'History click: {[str(prev) for prev in self.click_record]}')
            raise GameTooManyClickError(f'Too many click for a button: {count[0][0]}')
        if len(count) >= 2 and count[0][1] >= 6 and count[1][1] >= 6:
            logger.warning(f'Too many click between 2 buttons: {count[0][0]}, {count[1][0]}')
            logger.info(f'History click: {[str(prev) for prev in self.click_record]}')
            raise GameTooManyClickError(f'Too many click between 2 buttons: {count[0][0]}, {count[1][0]}')

        return False

    def click(self, button, record_check=True):
        """Method to click a button.

        Args:
            button (button.Button): AzurLane Button instance.
            record_check (bool):
        """
        if record_check:
            self.click_record_check(button)
        x, y = random_rectangle_point(button.button)
        logger.info(
            'Click %s @ %s' % (point2str(x, y), button)
        )
        method = self.config.DEVICE_CONTROL_METHOD
        if method == 'minitouch':
            self._click_minitouch(x, y)
        elif method == 'uiautomator2':
            self._click_uiautomator2(x, y)
        else:
            self._click_adb(x, y)
        self.sleep(self.config.SLEEP_AFTER_CLICK)

    @retry()
    def _click_uiautomator2(self, x, y):
        self.device.click(int(x), int(y))

    @retry()
    def _click_adb(self, x, y):
        self.adb_shell(['input', 'tap', str(x), str(y)])

    def multi_click(self, button, n, interval=(0.1, 0.2)):
        self.click_record_check(button)
        click_timer = Timer(0.1)
        for _ in range(n):
            remain = ensure_time(interval) - click_timer.current()
            if remain > 0:
                self.sleep(remain)

            click_timer.reset()
            self.click(button, record_check=False)

    def long_click(self, button, duration=(1, 1.2)):
        """Method to long click a button.

        Args:
            button (button.Button): AzurLane Button instance.
            duration(int, float, tuple):
        """
        x, y = random_rectangle_point(button.button)
        duration = ensure_time(duration)
        logger.info(
            'Click %s @ %s, %s' % (point2str(x, y), button, duration)
        )
        self.device.long_click(x, y, duration=duration)

    def swipe(self, vector, box=(123, 159, 1193, 628), random_range=(0, 0, 0, 0), padding=15, duration=(0.1, 0.2),
              name='SWIPE'):
        """Method to swipe.

        Args:
            box (tuple): Swipe in box (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
            vector (tuple): (x, y).
            random_range (tuple): (x_min, y_min, x_max, y_max).
            padding (int):
            duration (int, float, tuple):
            name (str): Swipe name
        """
        self.click_record_check(name)
        duration = ensure_time(duration)
        start, end = random_rectangle_vector(vector, box, random_range=random_range, padding=padding)
        logger.info(
            'Swipe %s -> %s, %s' % (point2str(*start), point2str(*end), duration)
        )
        if np.linalg.norm(np.subtract(start, end)) < 10:
            # Should swipe a certain distabce, otherwise AL will treat it as click.
            # uiautomator2 should >= 6px, minitouch should >= 5px
            logger.info('Swipe distance < 10px, dropped')
        fx, fy, tx, ty = np.append(start, end).tolist()

        method = self.config.DEVICE_CONTROL_METHOD
        if method == 'minitouch':
            self._swipe_minitouch(fx, fy, tx, ty)
        else:
            self.device.swipe(fx, fy, tx, ty, duration=duration)

    def drag_along(self, path):
        """Swipe following path.

        Args:
            path (list): (x, y, sleep)

        Examples:
            al.drag_along([
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
                logger.info(point2str(x, y) + ' down')
            elif index - length == -1:
                self.device.touch.up(x, y)
                logger.info(point2str(x, y) + ' up')
            else:
                self.device.touch.move(x, y)
                logger.info(point2str(x, y) + ' move')
            self.sleep(second)

    def drag(self, p1, p2, segments=1, shake=(0, 15), point_random=(-10, -10, 10, 10), shake_random=(-5, -5, 5, 5),
             swipe_duration=0.25, shake_duration=0.1):
        method = self.config.DEVICE_CONTROL_METHOD
        if method == 'minitouch':
            self._drag_minitouch(p1, p2, point_random=point_random)
        else:
            self._drag_uiautomator2(
                p1, p2, segments=segments, shake=shake, point_random=point_random, shake_random=shake_random,
                swipe_duration=swipe_duration, shake_duration=shake_duration)

    def _drag_uiautomator2(self, p1, p2, segments=1, shake=(0, 15), point_random=(-10, -10, 10, 10),
            shake_random=(-5, -5, 5, 5), swipe_duration=0.25, shake_duration=0.1):
        """Drag and shake, like:
                     /\
        +-----------+  +  +
                        \/
        A simple swipe or drag don't work well, because it only has two points.
        Add some way point to make it more like swipe.

        Args:
            p1 (tuple): Start point, (x, y).
            p2 (tuple): End point, (x, y).
            segments (int):
            shake (tuple): Shake after arrive end point.
            point_random: Add random to start point and end point.
            shake_random: Add random to shake array.
            swipe_duration: Duration between way points.
            shake_duration: Duration between shake points.
        """
        p1 = np.array(p1) - random_rectangle_point(point_random)
        p2 = np.array(p2) - random_rectangle_point(point_random)
        path = [(x, y, swipe_duration) for x, y in random_line_segments(p1, p2, n=segments, random_range=point_random)]
        path += [
            (*p2 + shake + random_rectangle_point(shake_random), shake_duration),
            (*p2 - shake - random_rectangle_point(shake_random), shake_duration),
            (*p2, shake_duration)
        ]
        path = [(int(x), int(y), d) for x, y, d in path]
        self.drag_along(path)
