from functools import wraps

import numpy as np

from module.logger import logger


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
        options = kwargs

        def decorate(func):
            name = func.__name__
            data = {'options': options, 'func': func}
            if name not in cls.func_list:
                cls.func_list[name] = [data]
            else:
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
                    if not np.all(flag):
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
