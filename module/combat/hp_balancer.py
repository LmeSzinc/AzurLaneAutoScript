import numpy as np

from module.base.base import ModuleBase
from module.base.button import color_similar
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
    hp = []
    hp_record = []
    _scout_order = (0, 1, 2)

    def _calculate_hp(self, location, size):
        """Calculate hp according to color.

        Args:
            location (tuple): Upper right of HP bar. (x, y)
            size (tuple): Size of HP bar. (x, y)

        Returns:
            float: HP.
        """
        area = np.append(np.array(location), np.array(location) + np.array(size))
        data = self.device.image.crop(area).resize((size[0], 1))
        data = [
            color_similar(pixel, COLOR_HP_GREEN) or color_similar(pixel, COLOR_HP_RED)
            for pixel in np.array(data)[0]
        ]
        data = np.sum(data) / size[0]
        return data

    def hp_get(self):
        """Get current HP from screenshot.

        Returns:
            list: HP(float) of 6 ship.
        """
        self.hp = [self._calculate_hp(loca, SIZE) for loca in LOCATION]
        logger.attr(
            'HP', ' '.join([str(int(data*100)).rjust(3)+'%' for data in self.hp])
        )
        return self.hp

    def hp_init(self):
        self.hp_get()
        self.hp_record = self.hp
        return self.hp

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
            hp = np.array(self.hp)[np.array(self.hp_record) > 0.3]
            if np.any(hp < self.config.LOW_HP_WITHDRAW_THRESHOLD):
                logger.info('Low HP withdraw triggered.')
                return True

        return False
