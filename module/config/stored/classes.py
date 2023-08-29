from datetime import datetime
from functools import cached_property as functools_cached_property

from module.base.decorator import cached_property
from module.config.utils import DEFAULT_TIME, deep_get, get_server_last_update
from module.exception import ScriptError


def now():
    return datetime.now().replace(microsecond=0)


def iter_attribute(cls):
    """
    Args:
        cls: Class or object

    Yields:
        str, obj: Attribute name, attribute value
    """
    for attr in dir(cls):
        if attr.startswith('_'):
            continue
        value = getattr(cls, attr)
        if type(value).__name__ in ['function', 'property']:
            continue
        yield attr, value


class StoredBase:
    time = DEFAULT_TIME

    def __init__(self, key):
        self._key = key
        self._config = None

    @cached_property
    def _name(self):
        return self._key.split('.')[-1]

    def _bind(self, config):
        """
        Args:
            config (AzurLaneConfig):
        """
        self._config = config

    @functools_cached_property
    def _stored(self):
        assert self._config is not None, 'StoredBase._bind() must be called before getting stored data'
        from module.logger import logger

        out = {}
        stored = deep_get(self._config.data, keys=self._key, default={})
        for attr, default in self._attrs.items():
            value = stored.get(attr, default)
            if attr == 'time':
                if not isinstance(value, datetime):
                    try:
                        value = datetime.fromisoformat(value)
                    except ValueError:
                        logger.warning(f'{self._name} has invalid attr: {attr}={value}, use default={default}')
                        value = default
            else:
                if not isinstance(value, type(default)):
                    logger.warning(f'{self._name} has invalid attr: {attr}={value}, use default={default}')
                    value = default

            out[attr] = value
        return out

    @cached_property
    def _attrs(self) -> dict:
        """
        All attributes defined
        """
        attrs = {
            # time is the first one
            'time': DEFAULT_TIME
        }
        for attr, value in iter_attribute(self.__class__):
            if attr.islower():
                attrs[attr] = value
        return attrs

    def __setattr__(self, key, value):
        if key in self._attrs:
            stored = self._stored
            stored['time'] = now()
            stored[key] = value
            self._config.modified[self._key] = stored
            if self._config.auto_update:
                self._config.update()
        else:
            super().__setattr__(key, value)

    def __getattribute__(self, item):
        if not item.startswith('_') and item in self._attrs:
            return self._stored[item]
        else:
            return super().__getattribute__(item)

    def is_expired(self) -> bool:
        return False

    def show(self):
        """
        Log self
        """
        from module.logger import logger
        logger.attr(self._name, self._stored)


class StoredExpiredAt0400(StoredBase):
    def is_expired(self):
        from module.logger import logger
        self.show()
        expired = self.time < get_server_last_update('04:00')
        logger.attr(f'{self._name} expired', expired)
        return expired


class StoredInt(StoredBase):
    value = 0


class StoredCounter(StoredBase):
    value = 0
    total = 0

    FIXED_TOTAL = 0

    def set(self, value, total=0):
        if self.FIXED_TOTAL:
            total = self.FIXED_TOTAL
        with self._config.multi_set():
            self.value = value
            self.total = total

    def to_counter(self) -> str:
        return f'{self.value}/{self.total}'

    def is_full(self) -> bool:
        return self.value >= self.total

    def get_remain(self) -> int:
        return self.total - self.value

    @cached_property
    def _attrs(self) -> dict:
        attrs = super()._attrs
        if self.FIXED_TOTAL:
            attrs['total'] = self.FIXED_TOTAL
        return attrs

    @functools_cached_property
    def _stored(self):
        stored = super()._stored
        if self.FIXED_TOTAL:
            stored['total'] = self.FIXED_TOTAL
        return stored


class StoredDailyActivity(StoredCounter, StoredExpiredAt0400):
    FIXED_TOTAL = 500


class StoredTrailblazePower(StoredCounter):
    FIXED_TOTAL = 180


class StoredDaily(StoredExpiredAt0400):
    quest1 = ''
    quest2 = ''
    quest3 = ''
    quest4 = ''
    quest5 = ''
    quest6 = ''

    def load_quests(self):
        """
        Returns:
            list[DailyQuest]: Note that must check if quests are expired
        """
        # DailyQuest should be lazy loaded
        from tasks.daily.keywords import DailyQuest
        quests = []
        for name in [self.quest1, self.quest2, self.quest3, self.quest4, self.quest5, self.quest6]:
            if not name:
                continue
            try:
                quest = DailyQuest.find(name)
                quests.append(quest)
            except ScriptError:
                pass
        return quests

    def write_quests(self, quests):
        """
        Args:
            quests (list[DailyQuest, str]):
        """
        from tasks.daily.keywords import DailyQuest
        quests = [q.name if isinstance(q, DailyQuest) else q for q in quests]
        with self._config.multi_set():
            try:
                self.quest1 = quests[0]
            except IndexError:
                self.quest1 = ''
            try:
                self.quest2 = quests[1]
            except IndexError:
                self.quest2 = ''
            try:
                self.quest3 = quests[2]
            except IndexError:
                self.quest3 = ''
            try:
                self.quest4 = quests[3]
            except IndexError:
                self.quest4 = ''
            try:
                self.quest5 = quests[4]
            except IndexError:
                self.quest5 = ''
            try:
                self.quest6 = quests[5]
            except IndexError:
                self.quest6 = ''


class StoredDungeonDouble(StoredExpiredAt0400):
    calyx = 0
    relic = 0
