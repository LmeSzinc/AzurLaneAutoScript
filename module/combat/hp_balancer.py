from module.base.base import ModuleBase
from module.base.button import *
from module.base.decorator import Config
from module.config.utils import to_list
from module.logger import logger

# Color that shows on HP bar.
COLOR_HP_GREEN = (156, 235, 57)
COLOR_HP_RED = (99, 44, 24)
SCOUT_POSITION = [(403, 421), (625, 369), (821, 326)]


class HPBalancer(ModuleBase):
    fleet_current_index = 1
    fleet_show_index = 1
    _hp = {}
    _hp_has_ship = {}

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

    def _calculate_hp(self, area):
        """Calculate hp according to color.

        Args:
            area (tuple):

        Returns:
            float: HP.
        """
        data = max(
            color_bar_percentage(self.device.image, area=area, prev_color=COLOR_HP_RED),
            color_bar_percentage(
                self.device.image, area=area, prev_color=COLOR_HP_GREEN
            ),
        )
        return data

    def _hp_grid(self):
        # Location of six HP bar, according to respective server for campaign
        if self.config.SERVER == "en":
            return ButtonGrid(
                origin=(35, 190),
                delta=(0, 100),
                button_shape=(66, 4),
                grid_shape=(1, 6),
            )
        elif self.config.SERVER == "jp":
            return ButtonGrid(
                origin=(35, 205),
                delta=(0, 100),
                button_shape=(66, 4),
                grid_shape=(1, 6),
            )
        else:
            return ButtonGrid(
                origin=(35, 206),
                delta=(0, 100),
                button_shape=(66, 4),
                grid_shape=(1, 6),
            )

    def hp_get(self):
        """Get current HP from screenshot.

        Returns:
            list: HP(float) of 6 ship.

        Logs:
            [HP]  98% ____ ____  98%  98%  98%
        """
        hp = [self._calculate_hp(button.area) for button in self._hp_grid().buttons]
        weight = to_list(self.config.HpControl_HpBalanceWeight)
        scout = np.array(hp[3:]) * np.array(weight) / np.max(weight)

        self.hp = hp[:3] + scout.tolist()
        if self.fleet_current_index not in self._hp_has_ship:
            self.hp_has_ship = [bool(hp > 0.3) for hp in self.hp]

        logger.attr(
            "HP",
            " ".join(
                [
                    str(int(data * 100)).rjust(3) + "%" if use else "____"
                    for data, use in zip(hp, self.hp_has_ship)
                ]
            ),
        )
        if np.sum(np.abs(np.diff(weight))) > 0:
            logger.attr(
                "HP_weight",
                " ".join([str(int(data * 100)).rjust(3) + "%" for data in self.hp]),
            )

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
        logger.info("scout_position_change (%s, %s)" % (p1, p2))
        self.device.drag(p1=SCOUT_POSITION[p1], p2=SCOUT_POSITION[p2], segments=3)

    def _expected_scout_order(self, hp):
        count = np.count_nonzero(hp)
        threshold = self.config.HpControl_HpBalanceThreshold

        if count == 3:
            descending = np.sort(hp)[::-1]
            sort = np.argsort(hp)[::-1]
            if descending[0] - descending[2] <= threshold:
                # 90% 80% 70%
                order = [0, 1, 2]
            elif descending[1] - descending[2] <= threshold / 2:
                # 95% 80% 70%
                order = [sort[0], 1, 2]
                order[sort[0]] = 0
            elif descending[0] - descending[1] <= threshold / 2:
                # 90% 80% 65%
                order = [0, sort[2], 2]
                order[sort[2]] = 1
            else:
                # 95% 80% 65%
                order = [sort[0], sort[2], sort[1]]
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
            logger.warning(f"HP invalid: {hp}")
            order = [0, 1, 2]

        return order

    @Config.when(DEVICE_CONTROL_METHOD="minitouch")
    def _gen_exchange_step(self, target):
        """
        Minitouch swiping is more like human, when it drag the first ship to the third ship,
        [0, 1, 2] becomes [1, 2, 0], while in adb/uiautomator2, it becomes [2, 1, 0].

        Args:
            target (list[int]): Such as [2, 0, 1].
        """
        diff = np.array(target) - np.array((0, 1, 2))
        count = np.count_nonzero(diff)
        if count == 3:
            if np.argsort(target)[0] == 1:
                # [0, 1, 2] -> [2, 0, 1]
                yield (2, 0)
            else:
                # [0, 1, 2] -> [1, 2, 0]
                yield (0, 2)
        elif count == 2:
            if np.argsort(target)[0] == 2:
                # [0, 1, 2] -> [1, 2, 0] -> [2, 1, 0]
                yield (0, 2)
                yield (1, 0)
            else:
                # [0, 2, 1]
                # [1, 0, 2]
                yield tuple(np.nonzero(diff)[0])
        elif count == 0:
            # [0, 1, 2]
            # Target is the same as origin. Do nothing
            pass

    @Config.when(DEVICE_CONTROL_METHOD=None)
    def _gen_exchange_step(self, target):
        """
        Args:
            target (list[int]): Such as [2, 0, 1].
        """
        diff = np.array(target) - np.array((0, 1, 2))
        count = np.count_nonzero(diff)
        if count == 3:
            yield (2, 0)
            if np.argsort(target)[0] == 1:
                # [0, 1, 2] -> [2, 1, 0] -> [2, 0, 1]
                yield (2, 1)
            else:
                # [0, 1, 2] -> [2, 1, 0] -> [1, 2, 0]
                yield (1, 0)
        elif count == 2:
            # [0, 2, 1]
            # [1, 0, 2]
            # [2, 1, 0]
            yield tuple(np.nonzero(diff)[0])
        elif count == 0:
            # [0, 1, 2]
            # Target is the same as origin. Do nothing
            pass

    def hp_balance(self):
        if self.config.Campaign_UseFleetLock:
            return False

        target = self._expected_scout_order(self.hp[3:])
        for step in self._gen_exchange_step(target):
            self._scout_position_change(*step)
            self.device.sleep(0.5)

        return True

    def hp_retreat_triggered(self):
        if self.config.HpControl_UseLowHpRetreat:
            hp = np.array(self.hp)[self.hp_has_ship]
            if np.any(hp < self.config.HpControl_LowHpRetreatThreshold):
                logger.info("Low HP retreat triggered.")
                return True

        return False
