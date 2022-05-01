import random
import re
from functools import wraps


class Config:
    """
    Decorator that calls different function with a same name according to config.

    func_list likes:
    func_list = {
        'func1': [
            {'options': {'ENABLE': True}, 'func': 1},
            {'options': {'ENABLE': False}, 'func': 1}
        ]
    }
    """
    func_list = {}

    @classmethod
    def when(cls, **kwargs):
        """
        Args:
            **kwargs: Any option in AzurLaneConfig.

        Examples:
            @Config.when(USE_ONE_CLICK_RETIREMENT=True)
            def retire_ships(self, amount=None, rarity=None):
                pass

            @Config.when(USE_ONE_CLICK_RETIREMENT=False)
            def retire_ships(self, amount=None, rarity=None):
                pass
        """
        from module.logger import logger
        options = kwargs

        def decorate(func):
            name = func.__name__
            data = {'options': options, 'func': func}
            if name not in cls.func_list:
                cls.func_list[name] = [data]
            else:
                override = False
                for record in cls.func_list[name]:
                    if record['options'] == data['options']:
                        record['func'] = data['func']
                        override = True
                if not override:
                    cls.func_list[name].append(data)

            @wraps(func)
            def wrapper(self, *args, **kwargs):
                """
                Args:
                    self: ModuleBase instance.
                    *args:
                    **kwargs:
                """
                for record in cls.func_list[name]:

                    flag = [value is None or self.config.__getattribute__(key) == value
                            for key, value in record['options'].items()]
                    if not all(flag):
                        continue

                    return record['func'](self, *args, **kwargs)

                logger.warning(f'No option fits for {name}, using the last define func.')
                return func(self, *args, **kwargs)

            return wrapper

        return decorate


class cached_property:
    """
    cached-property from https://github.com/pydanny/cached-property

    A property that is only computed once per instance and then replaces itself
    with an ordinary attribute. Deleting the attribute resets the property.
    Source: https://github.com/bottlepy/bottle/commit/fa7733e075da0d790d809aa3d2f53071897e6f76
    """

    def __init__(self, func):
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self

        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


def function_drop(rate=0.5, default=None):
    """
    Drop function calls to simulate random emulator stuck, for testing purpose.

    Args:
        rate (float): 0 to 1. Drop rate.
        default: Default value to return if dropped.

    Examples:
        @function_drop(0.3)
        def click(self, button, record_check=True):
            pass

        30% possibility:
        INFO | Dropped: module.device.device.Device.click(REWARD_GOTO_MAIN, record_check=True)
        70% possibility:
        INFO | Click (1091,  628) @ REWARD_GOTO_MAIN
    """
    from module.logger import logger

    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if random.uniform(0, 1) > rate:
                return func(*args, **kwargs)
            else:
                cls = ''
                arguments = [str(arg) for arg in args]
                if len(arguments):
                    matched = re.search('<(.*?) object at', arguments[0])
                    if matched:
                        cls = matched.group(1) + '.'
                        arguments.pop(0)
                arguments += [f'{k}={v}' for k, v in kwargs.items()]
                arguments = ', '.join(arguments)
                logger.info(f'Dropped: {cls}{func.__name__}({arguments})')
                return default

        return wrapper

    return decorate


def run_once(f):
    """
    Run a function only once, no matter how many times it has been called.

    Examples:
        @run_once
        def my_function(foo, bar):
            return foo + bar

        while 1:
            my_function()

    Examples:
        def my_function(foo, bar):
            return foo + bar

        action = run_once(my_function)
        while 1:
            action()
    """

    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return f(*args, **kwargs)

    wrapper.has_run = False
    return wrapper
