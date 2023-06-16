import datetime

from pydantic import BaseModel

from module.config.utils import DEFAULT_TIME
from module.logger import logger


def now():
    return datetime.datetime.now().replace(microsecond=0)


class StateValue(BaseModel):
    value: int = 0
    time: datetime.datetime = DEFAULT_TIME


TrailblazePowerMax = 180
ImmersifierMax = 8


class StateStorage(BaseModel):
    TrailblazePower = StateValue()
    Immersifier = StateValue()

    def __setattr__(self, key, value):
        if key in super().__getattribute__('__fields__'):
            storage = super().__getattribute__(key)
            storage.value = value
            storage.time = now()
        else:
            super().__setattr__(key, value)

    def __getattribute__(self, item):
        if item in super().__getattribute__('__fields__'):
            storage = super().__getattribute__(item)
            if storage.time == DEFAULT_TIME:
                logger.warning(f'Trying to get state {item} but it is never set')
            return storage.value
        else:
            return super().__getattribute__(item)


class StateMixin:
    state = StateStorage()
