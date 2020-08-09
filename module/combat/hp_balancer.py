from module.base.base import ModuleBase
from module.base.button import *
from module.logger import logger

# Location of six HP bar.
LOCATION = [
    (36, 195),
    (36, 295),
    (36, 395),
    (36, 497),
    (36, 597),
    (36, 697)
]
# HP bar size.
SIZE = (67, 4)
# Color that shows on HP bar.
COLOR_HP_GREEN = (156, 235, 57)
COLOR_HP_RED = (99, 44, 24)
SCOUT_POSITION = [
    (403, 421),
    (625, 369),
    (821, 326)
]


class HPBalancer(ModuleBase):
    fleet_current_index = 1
    _hp = {}
    _hp_has_ship = {}
    _scout_order = (0, 1, 2)

    @property
    def hp(self):
        """
        Returns:
            list[float]:
        """
        return self._hp[self.fleet_current_index]

    @hp.setter
    def hp(self, value):
        """
        Args:
            value (list[float]):
        """
        self._hp[self.fleet_current_index] = value

    @property
    def hp_has_ship(self):
        """
        Returns:
            list[bool]:
        """
        return self._hp_has_ship[self.fleet_current_index]

    @hp_has_ship.setter
    def hp_has_ship(self, value):
        """
        Args:
            value (list[float]):
        """
        self._hp_has_ship[self.fleet_current_index] = value

    def _calculate_hp(self, location, size):
        """Calculate hp according to color.

        Args:
            location (tuple): Upper right of HP bar. (x, y)
            size (tuple): Size of HP bar. (x, y)

        Returns:
            float: HP.
        """
        area = np.append(np.array(location), np.array(location) + np.array(size))
        data = max(
            color_bar_percentage(self.device.image, area=area, prev_color=COLOR_HP_RED),
            color_bar_percentage(self.device.image, area=area, prev_color=COLOR_HP_GREEN)
        )
        return data

    def hp_get(self):
        """Get current HP from screenshot.

        Returns:
            list: HP(float) of 6 ship.

        Logs:
            [HP]  98% ____ ____  98%  98%  98%
        """
        hp = [self._calculate_hp(loca, SIZE) for loca in LOCATION]
        scout = np.array(hp[3:]) * np.array(self.config.SCOUT_HP_WEIGHTS) / np.max(self.config.SCOUT_HP_WEIGHTS)

        self.hp = hp[:3] + scout.tolist()
        if self.fleet_current_index not in self._hp_has_ship:
            self.hp_has_ship = [bool(hp > 0.3) for hp in self.hp]

        logger.attr('HP', ' '.join(
            [str(int(data * 100)).rjust(3) + '%' if use else '____' for data, use in zip(hp, self.hp_has_ship)]))
        if np.sum(np.abs(np.diff(self.config.SCOUT_HP_WEIGHTS))) > 0:
            logger.attr('HP_weight', ' '.join([str(int(data * 100)).rjust(3) + '%' for data in self.hp]))

        return self.hp

    def hp_reset(self):
        """
        Call this method after enter map.
        """
        self._hp = {}
        self._hp_has_ship = {}

    def _scout_position_change(self, p1, p2):
        """Exchange KAN-SEN's position.
        It need to move up and down a little, even though it moves to the right location.

        Args:
            p1 (int): Origin position [0, 2].
            p2 (int): Target position [0, 2].
        """
        logger.info('scout_position_change (%s, %s)' % (p1, p2))
        self.device.drag(p1=SCOUT_POSITION[p1], p2=SCOUT_POSITION[p2], segments=3)

    def _expected_scout_order(self, hp):
        count = np.count_nonzero(hp)
        threshold = self.config.SCOUT_HP_DIFFERENCE_THRESHOLD

        if count == 3:
            descending = np.sort(hp)[::-1]
            sort = np.argsort(hp)[::-1]
            if descending[0] - descending[2] > threshold:
                if descending[1] - descending[2] > threshold:
                    # 100% 70% 40%
                    order = [sort[0], sort[2], sort[1]]
                else:
                    # 100% 70% 60%
                    order = [sort[0], 1, 2]
                    order[sort[0]] = 0
            else:
                # 80% 80% 80%
                order = [0, 1, 2]
        elif count == 2:
            if hp[1] - hp[0] > threshold:
                # 70% 100% 0%
                order = [1, 0, 2]
            else:
                # 100% 70% 0%
                order = [0, 1, 2]
        elif count == 1:
            # 80% 0% 0%
            order = [0, 1, 2]
        else:
            logger.warning(f'HP invalid: {hp}')
            order = [0, 1, 2]

        return order

    @staticmethod
    def _gen_exchange_step(origin, target):
        diff = np.array(target) - np.array(origin)
        count = np.count_nonzero(diff)
        if count == 3:
            yield (2, 0)
            if np.argsort(target)[0] - np.argsort(origin)[0] == 1:
                yield (2, 1)
            else:
                yield (1, 0)
        elif count == 2:
            yield tuple(np.nonzero(diff)[0])
        elif count == 0:
            # Target is the same as origin. Do nothing
            pass

    def hp_balance(self):
        if self.config.ENABLE_MAP_FLEET_LOCK:
            return False

        target = self._expected_scout_order(self.hp[3:])
        for step in self._gen_exchange_step(self._scout_order, target):
            self._scout_position_change(*step)
            self.device.sleep(0.5)

        return True

    def hp_withdraw_triggered(self):
        if self.config.ENABLE_LOW_HP_WITHDRAW:
            hp = np.array(self.hp)[self.hp_has_ship]
            if np.any(hp < self.config.LOW_HP_WITHDRAW_THRESHOLD):
                logger.info('Low HP withdraw triggered.')
                return True

        return False
