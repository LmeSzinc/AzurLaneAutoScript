import time
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

    def show(self):
        logger.info('%s s' % str(self.current()))
