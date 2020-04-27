import time
from datetime import datetime, timedelta
from functools import wraps

from module.logger import logger


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
        datetime: Time with given hour, minute, second in the future.
    """
    hour, minute = [int(x) for x in string.split(':')]
    future = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
    future = future + timedelta(days=1) if future < datetime.now() else future
    return future


class Timer:
    def __init__(self, limit):
        self.limit = limit
        self._current = 0

    def start(self):
        if not self.started():
            self._current = time.time()

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
        return time.time() - self._current > self.limit

    def reset(self):
        self._current = time.time()

    def wait(self):
        """
        Wait until timer reached.
        """
        diff = self._current + self.limit - time.time()
        if diff > 0:
            time.sleep(diff)

    def show(self):
        logger.info('%s s' % str(self.current()))
