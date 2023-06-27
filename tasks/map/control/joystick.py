from functools import cached_property

from module.base.timer import Timer
from module.logger import logger
from tasks.base.ui import UI
from tasks.map.assets.assets_map_control import *


class MapControlJoystick(UI):
    _map_A_timer = Timer(1)
    _map_E_timer = Timer(1)
    _map_run_timer = Timer(1)

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

    def handle_map_run(self):
        """
        Keep character running.
        Note that RUN button can only be clicked when character is moving.

        Returns:
            bool: If clicked.
        """
        is_running = self.image_color_count(RUN_BUTTON, color=(208, 183, 138), threshold=221, count=100)

        if not is_running and self._map_run_timer.reached():
            self.device.click(RUN_BUTTON)
            self._map_run_timer.reset()
            return True

        return False
