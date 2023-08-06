from functools import cached_property

from module.base.timer import Timer
from module.logger import logger
from tasks.map.assets.assets_map_control import ROTATION_SWIPE_AREA
from tasks.map.control.joystick import MapControlJoystick
from tasks.map.minimap.minimap import Minimap


class MapControl(MapControlJoystick):
    _rotation_swipe_interval = Timer(1.2, count=2)

    @cached_property
    def minimap(self) -> Minimap:
        return Minimap()

    def handle_rotation_set(self, target, threshold=15):
        """
        Set rotation while running.
        self.minimap.update_rotation() must be called first.

        Args:
            target: Target degree (0~360)
            threshold:

        Returns:
            bool: If swiped rotation
        """
        if self.minimap.is_rotation_near(target, threshold=threshold):
            return False
        if not self._rotation_swipe_interval.reached():
            return False

        logger.info(f'Rotation set: {target}')
        diff = self.minimap.rotation_diff(target) * self.minimap.ROTATION_SWIPE_MULTIPLY
        diff = min(diff, self.minimap.ROTATION_SWIPE_MAX_DISTANCE)
        diff = max(diff, -self.minimap.ROTATION_SWIPE_MAX_DISTANCE)

        self.device.swipe_vector((-diff, 0), box=ROTATION_SWIPE_AREA.area, duration=(0.2, 0.5))
        self._rotation_swipe_interval.reset()
        return True

    def rotation_set(self, target, threshold=15, skip_first_screenshot=False):
        """
        Set rotation while standing.

        Args:
            target: Target degree (0~360)
            threshold:
            skip_first_screenshot:

        Returns:
            bool: If swiped rotation
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
                self.minimap.update_rotation(self.device.image)
                self.minimap.log_minimap()

            # End
            if self.minimap.is_rotation_near(target, threshold=threshold):
                logger.info(f'Rotation is now at: {target}')
                break

            if self.handle_rotation_set(target, threshold=threshold):
                continue
