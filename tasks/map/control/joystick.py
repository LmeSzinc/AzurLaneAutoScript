import math
from functools import cached_property

from module.base.timer import Timer
from module.device.method.maatouch import MaatouchBuilder
from module.device.method.minitouch import CommandBuilder, insert_swipe, random_normal_distribution
from module.exception import ScriptError
from module.logger import logger
from tasks.base.ui import UI
from tasks.map.assets.assets_map_control import *


class JoystickContact:
    CENTER = (JOYSTICK.area[0] + JOYSTICK.area[2]) / 2, (JOYSTICK.area[1] + JOYSTICK.area[3]) / 2
    # Minimum radius 49px
    RADIUS_WALK = (55, 65)
    # Minimum radius 103px
    RADIUS_RUN = (105, 115)

    def __init__(self, main):
        """
        Args:
            main (MapControlJoystick):
        """
        self.main = main
        self.prev_point = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Lift finger when:
        - Walk event ends, JoystickContact ends
        - Any error is raised
        Can not lift finger when:
        - Process is force terminated
        """
        builder = self.builder
        if self.is_downed:
            builder.up().commit()
            builder.send()
            logger.info('JoystickContact ends')
        else:
            logger.info('JoystickContact ends but it was never downed')

    @property
    def is_downed(self):
        return self.prev_point is not None

    @cached_property
    def builder(self):
        """
        Initialize a command builder
        """
        method = self.main.config.Emulator_ControlMethod
        if method == 'MaaTouch':
            # Get the very first builder to initialize MaaTouch
            _ = self.main.device.maatouch_builder
            builder = MaatouchBuilder(self.main.device, contact=1)
        elif method == 'minitouch':
            # Get the very first builder to initialize minitouch
            _ = self.main.device.minitouch_builder
            builder = CommandBuilder(self.main.device, contact=1)
        else:
            raise ScriptError(f'Control method {method} does not support multi-finger, '
                              f'please use MaaTouch or minitouch instead')

        # def empty_func():
        #     pass
        #
        # # No clear()
        # builder.clear = empty_func
        # No delay
        builder.DEFAULT_DELAY = 0.

        return builder

    @classmethod
    def direction2screen(cls, direction, run=True):
        """
        Args:
            direction (int, float): Direction to goto (0~360)
            run: True for character running, False for walking

        Returns:
            tuple[int, int]: Position on screen to control joystick
        """
        direction += random_normal_distribution(-5, 5, n=5)
        radius = cls.RADIUS_RUN if run else cls.RADIUS_WALK
        radius = random_normal_distribution(*radius, n=5)

        direction = math.radians(direction)
        point = (
            cls.CENTER[0] + radius * math.sin(direction),
            cls.CENTER[1] - radius * math.cos(direction),
        )
        point = (int(round(point[0])), int(round(point[1])))
        return point

    def set(self, direction, run=True):
        """
        Set joystick to given position

        Args:
            direction (int, float): Direction to goto (0~360)
            run: True for character running, False for walking
        """
        logger.info(f'JoystickContact set to {direction}')
        point = JoystickContact.direction2screen(direction, run=run)
        builder = self.builder

        if self.is_downed:
            points = insert_swipe(p0=self.prev_point, p3=point, speed=20)
            for point in points[1:]:
                builder.move(*point).commit().wait(10)
            builder.send()
        else:
            builder.down(*point).commit()
            builder.send()
            # Character starts moving, RUN button is still unavailable in a short time.
            # Assume available in 0.3s
            # We still have reties if 0.3s is incorrect.
            self.main._map_2x_run_timer.set_current(0.7)

        self.prev_point = point


class MapControlJoystick(UI):
    _map_A_timer = Timer(1)
    _map_E_timer = Timer(1)
    _map_2x_run_timer = Timer(1)

    @cached_property
    def joystick_center(self) -> tuple[float, float]:
        x1, y1, x2, y2 = JOYSTICK.area
        return (x1 + x2) / 2, (y1 + y2) / 2

    def map_get_technique_points(self):
        """
        Returns:
            int: 0 to 5.
        """
        points = [
            self.image_color_count(button, color=(255, 255, 255), threshold=221, count=20)
            for button in [
                TECHNIQUE_POINT_1,
                TECHNIQUE_POINT_2,
                TECHNIQUE_POINT_3,
                TECHNIQUE_POINT_4,
                TECHNIQUE_POINT_5,
            ]
        ]
        count = sum(points)
        logger.attr('TechniquePoints', count)
        return count

    def handle_map_A(self):
        """
        Simply clicking A with an interval of 1s, no guarantee of success.

        Returns:
            bool: If clicked.
        """
        if self._map_A_timer.reached():
            self.device.click(A_BUTTON)
            self._map_A_timer.reset()
            return True

        return False

    def handle_map_E(self):
        """
        Simply clicking E with an interval of 1s, no guarantee of success.
        Note that E cannot be released if technique points ran out.

        Returns:
            bool: If clicked.
        """
        if self._map_E_timer.reached():
            self.device.click(E_BUTTON)
            self._map_E_timer.reset()
            return True

        return False

    def handle_map_2x_run(self, run=True):
        """
        Keep character running.
        Note that RUN button can only be clicked when character is moving.

        Returns:
            bool: If clicked.
        """
        is_running = self.image_color_count(RUN_BUTTON, color=(208, 183, 138), threshold=221, count=100)

        if run and not is_running and self._map_2x_run_timer.reached():
            self.device.click(RUN_BUTTON)
            self._map_2x_run_timer.reset()
            return True
        if not run and is_running and self._map_2x_run_timer.reached():
            self.device.click(RUN_BUTTON)
            self._map_2x_run_timer.reset()
            return True

        return False
