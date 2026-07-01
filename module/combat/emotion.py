from datetime import datetime
from time import sleep

import numpy as np

from module.base.decorator import cached_property
from module.base.utils import random_normal_distribution_int
from module.config.config import AzurLaneConfig
from module.exception import ScriptEnd, ScriptError, RequestHumanTakeover
from module.logger import logger

DIC_LIMIT = {
    'keep_exp_bonus': 120,
    'prevent_green_face': 40,
    'prevent_yellow_face': 30,
    'prevent_red_face': 2,
}
DIC_RECOVER = {
    'not_in_dormitory': 20,
    'dormitory_floor_1': 40,
    'dormitory_floor_2': 50,
}
DIC_RECOVER_MAX = {
    'not_in_dormitory': 119,
    'dormitory_floor_1': 150,
    'dormitory_floor_2': 150,
}
OATH_RECOVER = 10


class FleetEmotion:
    def __init__(self, config, fleet):
        """
        Args:
            config (AzurLaneConfig):
            fleet (int): Fleet index
        """
        self.config = config
        self.fleet = fleet
        self.current = 0

    @property
    def value(self):
        """
        Returns:
            int: 0 to 150
        """
        return getattr(self.config, f'Emotion_Fleet{self.fleet}Value')

    @property
    def value_name(self):
        """
        Returns:
            str:
        """
        return f'Emotion_Fleet{self.fleet}Value'

    @property
    def record(self):
        """
        Returns:
            datetime.datetime:
        """
        return getattr(self.config, f'Emotion_Fleet{self.fleet}Record')

    @property
    def recover(self):
        """
        Returns:
            str: not_in_dormitory, dormitory_floor_1, dormitory_floor_2
        """
        return getattr(self.config, f'Emotion_Fleet{self.fleet}Recover')

    @property
    def control(self):
        """
        Returns:
            str: keep_exp_bonus, prevent_green_face, prevent_yellow_face, prevent_red_face
        """
        return getattr(self.config, f'Emotion_Fleet{self.fleet}Control')

    @property
    def oath(self):
        """
        Returns:
            bool: If all ships oath.
        """
        return getattr(self.config, f'Emotion_Fleet{self.fleet}Oath')

    @property
    def speed(self):
        """
        Returns:
            int: Recover speed per 6 min.
        """
        speed = DIC_RECOVER[self.recover]
        if self.oath:
            speed += OATH_RECOVER
        return speed // 10

    @property
    def limit(self):
        """
        Returns:
            int: Minimum emotion value to control
        """
        return DIC_LIMIT[self.control]

    @property
    def max(self):
        """
        Returns:
            int: Maximum emotion value
        """
        return DIC_RECOVER_MAX[self.recover]

    def update(self):
        recover_count = int(int(datetime.now().timestamp()) // 360 - int(self.record.timestamp()) // 360)
        recover_count = max(recover_count, 0)
        self.current = min(max(self.value, 0) + self.speed * recover_count, self.max)

    def get_recovered(self, expected_reduce=0, control_limit=None):
        """
        Args:
            expected_reduce (int):
            control_limit (int, None): Use configured control limit if None.

        Returns:
            datetime.datetime: When will emotion >= control limit + expected reduce.
                If already recovered, return time in the past.
        """
        limit = self.limit if control_limit is None else control_limit
        if control_limit is None and self.control == 'keep_exp_bonus' and self.recover == 'not_in_dormitory':
            logger.critical(f'Fleet {self.fleet} Emotion Control=\"Keep Happy Bonus\" and '
                            f'Fleet {self.fleet} Recover Location=\"Docks\" can not be used together, '
                            'please check your emotion settings')
            raise RequestHumanTakeover
        # In 14-4 with 2X book, expected emotion reduce is 32, can't keep happy bonus (>120),
        # otherwise will infinite task delay
        if control_limit is None and self.control == 'keep_exp_bonus' and expected_reduce >= 29:
            expected_reduce = 29
            logger.info(f'Fleet {self.fleet} expected_reduce is limited to 29 '
                        f'when Emotion Control=\"Keep Happy Bonus\"')

        recover_count = (limit + expected_reduce - self.current) // self.speed
        recovered = (int(datetime.now().timestamp()) // 360 + recover_count + 1) * 360
        return datetime.fromtimestamp(recovered)


class Emotion:
    total_reduced = 0
    map_is_2x_book = False

    def __init__(self, config):
        """
        Args:
            config (AzurLaneConfig):
        """
        self.config = config
        self.fleet_1 = FleetEmotion(self.config, fleet=1)
        self.fleet_2 = FleetEmotion(self.config, fleet=2)
        self.fleets = [self.fleet_1, self.fleet_2]
        self.reset_campaign()

    @property
    def is_calculate(self):
        return 'calculate' in self.config.Emotion_Mode

    @property
    def is_ignore(self):
        return 'ignore' in self.config.Emotion_Mode

    def update(self):
        """
        Update emotion value. This should be called before doing anything.
        """
        for fleet in self.fleets:
            fleet.update()

    def record(self):
        """
        Save current emotion value to config.
        """
        value = {}
        for fleet in self.fleets:
            value[fleet.value_name] = fleet.current

        self.config.set_record(**value)

    def show(self):
        for fleet in self.fleets:
            logger.attr(f'Emotion fleet_{fleet.fleet}', fleet.value)

    @property
    def reduce_per_battle(self):
        if self.map_is_2x_book:
            return 4
        else:
            return 2

    @property
    def reduce_per_battle_before_entering(self):
        if self.map_is_2x_book:
            return 4
        elif self.config.Campaign_Use2xBook:
            return 4
        else:
            return 2

    def reset_campaign(self):
        self.low_emotion_triggered = False
        self.fleets_used_in_campaign = set()

    @staticmethod
    def _valid_fleet_index(fleet_index):
        try:
            fleet_index = int(fleet_index)
        except (TypeError, ValueError):
            return None

        if fleet_index in [1, 2]:
            return fleet_index
        return None

    def _fleet_indexes(self, fleet_index=None):
        if isinstance(fleet_index, (list, tuple, set)):
            indexes = [
                index for index in [self._valid_fleet_index(index) for index in fleet_index]
                if index is not None
            ]
            return sorted(set(indexes)) if indexes else [1, 2]

        index = self._valid_fleet_index(fleet_index)
        if index is not None:
            return [index]
        return [1, 2]

    def _expected_reduce(self, battle):
        method = self.config.Fleet_FleetOrder

        if method == 'fleet1_mob_fleet2_boss':
            battle = (battle - 1, 1)
        elif method == 'fleet1_boss_fleet2_mob':
            battle = (1, battle - 1)
        elif method == 'fleet1_all_fleet2_standby':
            battle = (battle, 0)
        elif method == 'fleet1_standby_fleet2_all':
            battle = (0, battle)
        else:
            raise ScriptError(f'Unknown fleet order: {method}')

        battle = tuple(np.array(battle) * self.reduce_per_battle_before_entering)
        logger.info(f'Expect emotion reduce: {battle}')
        return battle

    def _get_recovered(self, battle):
        battle = self._expected_reduce(battle)
        self.update()
        self.record()
        self.show()
        return max([f.get_recovered(b) for f, b in zip(self.fleets, battle)])

    def delay_before_entering_map(self, battle, fleet_index=None):
        """
        Delay current task when low emotion is reported before the map is entered.

        Args:
            battle (int): Battles in this campaign.
            fleet_index (int, None): 1 or 2. Unknown fleets reset both ledgers.

        Raise:
            ScriptEnd: Stop current task normally so scheduler can continue.
        """
        logger.hr('Emotion control')
        self.reset_low_emotion(fleet_index=fleet_index)
        recovered = self._get_recovered(battle)
        logger.info(f'Delay current task until emotion recovers at {recovered}')
        self.config.task_delay(target=recovered)
        raise ScriptEnd('Emotion control')

    def delay_after_campaign(self, battle):
        """
        Delay current task after a map ended if low emotion control happened in this map.

        Args:
            battle (int): Battles in this campaign.

        Returns:
            bool: If delayed.
        """
        if not self.is_calculate or not self.low_emotion_triggered:
            self.reset_campaign()
            return False

        indexes = sorted(self.fleets_used_in_campaign)
        if not indexes:
            logger.warning('Low emotion triggered but no battle fleet was recorded')
            self.reset_campaign()
            return False

        logger.hr('Emotion control after campaign')
        recovered = self._get_recovered(battle)
        self.reset_campaign()
        if recovered > datetime.now():
            logger.info(f'Delay current task until next run emotion recovers at {recovered}')
            self.config.task_delay(target=recovered)
            return True
        return False

    def register_battle_fleet(self, fleet_index):
        try:
            fleet_index = int(fleet_index)
        except (TypeError, ValueError):
            return

        if fleet_index in [1, 2]:
            self.fleets_used_in_campaign.add(fleet_index)

    def reset_low_emotion(self, fleet_index=None):
        """
        Reset emotion ledger after the game client reports low emotion.

        Args:
            fleet_index (int, None): 1 or 2. Unknown fleets reset both ledgers.

        Returns:
            list[FleetEmotion]: Fleets whose values were reset.
        """
        indexes = self._fleet_indexes(fleet_index=fleet_index)
        if len(indexes) > 1 and not isinstance(fleet_index, (list, tuple, set)):
            logger.warning('Unable to identify low-emotion fleet, reset both fleet ledgers')

        logger.hr('Emotion control')
        self.update()
        fleets = [self.fleets[index - 1] for index in indexes]
        for fleet in fleets:
            fleet.current = 0
            logger.info(f'Reset emotion fleet {fleet.fleet} to {fleet.current}')

        self.record()
        self.show()
        return fleets

    def wait_after_low_emotion(self, fleet_index=None):
        """
        Wait in map after backing out of the low-emotion sortie popup.
        """
        self.low_emotion_triggered = True
        fleets = self.reset_low_emotion(fleet_index=fleet_index)
        for fleet in fleets:
            self.wait(fleet_index=fleet.fleet, control_limit=0, check_task_switch=True)

    def check_reduce(self, battle):
        """
        Check emotion before entering a campaign.

        Args:
            battle (int): Battles in this campaign

        Raise:
            ScriptEnd: Delay current task to prevent emotion control in the future.
        """
        if not self.is_calculate:
            return

        recovered = self._get_recovered(battle)
        if recovered > datetime.now():
            logger.info('Delay current task to prevent emotion control in the future')
            self.config.task_delay(target=recovered)
            raise ScriptEnd('Emotion control')

    def wait(self, fleet_index, control_limit=None, check_task_switch=False):
        """
        Wait emotion of specific fleet.
        Should be called before entering any battles.

        Args:
            fleet_index (int): 1 or 2.
            control_limit (int, None): Use configured control limit if None.
            check_task_switch (bool): If check scheduler switch while waiting.
        """
        self.update()
        self.record()
        self.show()
        fleet = self.fleets[fleet_index - 1]
        expected_reduce = self.reduce_per_battle
        recovered = fleet.get_recovered(expected_reduce=expected_reduce, control_limit=control_limit)
        if recovered > datetime.now():
            logger.hr('Emotion wait')
            limit = fleet.limit if control_limit is None else control_limit
            logger.info(
                f'Emotion of fleet {fleet_index} will recover to {limit + expected_reduce} at {recovered}'
            )

            wait_interval = 5 if check_task_switch else 60
            log_count = 0
            while 1:
                if datetime.now() > recovered:
                    break
                if check_task_switch and self.config.task_switched():
                    logger.info('Task switched during emotion wait')
                    raise ScriptEnd('Emotion control')

                if log_count <= 0:
                    logger.attr('Wait until', recovered)
                    log_count = 12 if check_task_switch else 1
                log_count -= 1
                sleep(wait_interval)

    def reduce(self, fleet_index):
        """
        Reduce emotion of specific fleet.
        Should be called after battle executing.
        On server side, emotion is reduced once battle loading finished.

        Args:
            fleet_index (int): 1 or 2.
        """
        logger.hr('Emotion reduce')
        self.update()

        fleet_index = int(fleet_index)
        self.register_battle_fleet(fleet_index)
        fleet = self.fleets[fleet_index - 1]
        fleet.current -= self.reduce_per_battle
        self.total_reduced += self.reduce_per_battle
        self.record()
        self.show()

    @cached_property
    def bug_threshold(self):
        """
        Returns:
            int:
        """
        return random_normal_distribution_int(55, 105, n=2)

    def bug_threshold_reset(self):
        """ Call this method after emotion bug triggered. """
        del self.__dict__['bug_threshold']

    def triggered_bug(self):
        """
        Azur Lane client does not calculate emotion correctly, which is a bug.
        After a long run, we have to restart game client and let the client update it.
        """
        logger.attr('Emotion_bug', f'{self.total_reduced}/{self.bug_threshold}')
        if self.total_reduced >= self.bug_threshold:
            logger.info('Azur Lane client does not calculate emotion correctly, which is a bug. '
                        'After a long run, we have to restart game client and let the client update it.')
            self.total_reduced = 0
            self.bug_threshold_reset()
            return True
        else:
            return False
