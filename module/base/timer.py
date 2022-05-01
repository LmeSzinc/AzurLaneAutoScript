import time
from datetime import datetime, timedelta
from functools import wraps


def timer(function):
    @wraps(function)
    def function_timer(*args, **kwargs):
        t0 = time.time()

        result = function(*args, **kwargs)
        t1 = time.time()
        print('%s: %s s' % (function.__name__, str(round(t1 - t0, 10))))
        return result
    return function_timer


def future_time(string):
    """
    Args:
        string (str): Such as 14:59.

    Returns:
        datetime.datetime: Time with given hour, minute in the future.
    """
    hour, minute = [int(x) for x in string.split(':')]
    future = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
    future = future + timedelta(days=1) if future < datetime.now() else future
    return future


def past_time(string):
    """
    Args:
        string (str): Such as 14:59.

    Returns:
        datetime.datetime: Time with given hour, minute in the past.
    """
    hour, minute = [int(x) for x in string.split(':')]
    past = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
    past = past - timedelta(days=1) if past > datetime.now() else past
    return past


def future_time_range(string):
    """
    Args:
        string (str): Such as 23:30-06:30.

    Returns:
        tuple(datetime.datetime): (time start, time end).
    """
    start, end = [future_time(s) for s in string.split('-')]
    if start > end:
        start = start - timedelta(days=1)
    return start, end


def time_range_active(time_range):
    """
    Args:
        time_range(tuple(datetime.datetime)): (time start, time end).

    Returns:
        bool:
    """
    return time_range[0] < datetime.now() < time_range[1]


class Timer:
    def __init__(self, limit, count=0):
        """
        Args:
            limit (int, float): Timer limit
            count (int): Timer reach confirm count. Default to 0.
                When using a structure like this, must set a count.
                Otherwise it goes wrong, if screenshot time cost greater than limit.

                if self.appear(MAIN_CHECK):
                    if confirm_timer.reached():
                        pass
                else:
                    confirm_timer.reset()

                Also, It's a good idea to set `count`, to make alas run more stable on slow computers.
                Expected speed is 0.35 second / screenshot.
        """
        self.limit = limit
        self.count = count
        self._current = 0
        self._reach_count = count

    def start(self):
        if not self.started():
            self._current = time.time()
            self._reach_count = 0

        return self

    def started(self):
        return bool(self._current)

    def current(self):
        """
        Returns:
            float
        """
        return time.time() - self._current

    def reached(self):
        """
        Returns:
            bool
        """
        self._reach_count += 1
        return time.time() - self._current > self.limit and self._reach_count > self.count

    def reset(self):
        self._current = time.time()
        self._reach_count = 0

    def clear(self):
        self._current = 0
        self._reach_count = self.count

    def reached_and_reset(self):
        """
        Returns:
            bool:
        """
        if self.reached():
            self.reset()
            return True
        else:
            return False

    def wait(self):
        """
        Wait until timer reached.
        """
        diff = self._current + self.limit - time.time()
        if diff > 0:
            time.sleep(diff)

    def show(self):
        from module.logger import logger
        logger.info('%s s' % str(self.current()))
