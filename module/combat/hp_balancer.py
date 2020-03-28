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
# If difference greater than this, change position.
SCOUT_HP_DIFFERENCE_THRESHOLD = 0.2
SCOUT_POSITION = [
    (403, 421),
    (625, 369),
    (821, 326)
]
# Give a normal distribution random offset when swiping to a point.
# (x_min, y_min, x_max, y_max).
POINT_OFFSET = (0, 0, 0, 0)
# Give a normal distribution random offset when moving up and down.
# (x_min, y_min, x_max, y_max).
UP_OFFSET = (0, 10, 0, 10)
DOWN_OFFSET = (0, -10, 0, -10)


class HPBalancer(ModuleBase):
    hp = []
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
        data = self.image.crop(area).resize((size[0], 1))
        data = [
            color_similar(pixel, COLOR_HP_GREEN) or color_similar(pixel, COLOR_HP_RED)
            for pixel in np.array(data)[0]
        ]
        data = np.sum(data) / size[0]
        return data

    def get_hp(self):
        """Get current HP from screenshot.

        Returns:
            list: HP(float) of 6 ship.
        """
        self.hp = [self._calculate_hp(loca, SIZE) for loca in LOCATION]
        logger.info(
            'HP:' + ' '.join([str(int(data*100)).rjust(3)+'%' for data in self.hp])
        )
        return self.hp

    def scout_position_change(self, p1, p2):
        """Exchange KAN-SEN's position.
        It need to move up and down a little, even though it moves to the right location.

        Args:
            p1 (int): Origin position [0, 2].
            p2 (int): Target position [0, 2].
        """
        logger.info('scout_position_change (%s, %s)' % (p1, p2))
        p1 = self.drag_node(SCOUT_POSITION[p1], POINT_OFFSET, 0.25)
        p2 = self.drag_node(SCOUT_POSITION[p2], POINT_OFFSET, 0.1)
        path = [
            p1,
            p2,
            self.drag_node(p2[:2], UP_OFFSET, 0.1),
            self.drag_node(p2[:2], DOWN_OFFSET, 0.1),
            p2
        ]
        self.drag(path)

    @staticmethod
    def _expected_scout_order(hp):
        descending = np.sort(hp)[::-1]
        sort = np.argsort(hp)[::-1]

        if descending[0] - descending[2] > SCOUT_HP_DIFFERENCE_THRESHOLD:
            if descending[1] - descending[2] > SCOUT_HP_DIFFERENCE_THRESHOLD:
                # 100% 70% 40%
                order = [sort[0], sort[2], sort[1]]
            else:
                # 100% 70% 60%
                order = [sort[0], 1, 2]
                order[sort[0]] = 0
        else:
            # 80% 80% 80%
            order = [0, 1, 2]
        return order

    @staticmethod
    def _gen_exchange_step(origin, target):
        diff = np.array(target) - np.array(origin)
        count = np.count_nonzero(diff)
        if count == 3:
            yield (0, 2)
            if np.argsort(target)[0] - np.argsort(origin)[0] == 1:
                yield (1, 2)
            else:
                yield (0, 1)
        elif count == 2:
            yield tuple(np.nonzero(diff)[0])
        elif count == 0:
            # Target is the same as origin. Do nothing
            pass

    def balance_scout_hp(self):
        target = self._expected_scout_order(self.hp[3:])
        for step in self._gen_exchange_step(self._scout_order, target):
            self.scout_position_change(*step)
            self.sleep(0.5)
