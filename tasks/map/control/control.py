from functools import cached_property

from module.base.timer import Timer
from module.logger import logger
from tasks.map.assets.assets_map_control import ROTATION_SWIPE_AREA
from tasks.map.control.joystick import JoystickContact, MapControlJoystick
from tasks.map.control.waypoint import Waypoint, ensure_waypoint
from tasks.map.minimap.minimap import Minimap
from tasks.map.resource.const import diff_to_180_180


class MapControl(MapControlJoystick):
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

        # if abs(self.minimap.rotation_diff(target)) > 60:
        #     self.device.image_save()
        #     exit(1)

        logger.info(f'Rotation set: {target}')
        diff = self.minimap.rotation_diff(target) * self.minimap.ROTATION_SWIPE_MULTIPLY
        diff = min(diff, self.minimap.ROTATION_SWIPE_MAX_DISTANCE)
        diff = max(diff, -self.minimap.ROTATION_SWIPE_MAX_DISTANCE)

        self.device.swipe_vector((-diff, 0), box=ROTATION_SWIPE_AREA.area, duration=(0.2, 0.5))
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
        interval = Timer(1, count=2)
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

            if interval.reached():
                if self.handle_rotation_set(target, threshold=threshold):
                    interval.reset()
                    continue

    def _goto(
            self,
            contact: JoystickContact,
            waypoint: Waypoint,
            end_opt=True,
            skip_first_screenshot=False
    ):
        """
        Point to point walk.

        Args:
            contact:
                JoystickContact, must be wrapped with:
                `with JoystickContact(self) as contact:`
            waypoint:
                Position to goto, (x, y)
            end_opt:
                True to enable endpoint optimizations,
                character will smoothly approach target position
            skip_first_screenshot:
        """
        logger.hr('Goto', level=2)
        logger.info(f'Goto {waypoint}')
        self.device.stuck_record_clear()
        self.device.click_record_clear()

        end_opt = end_opt and waypoint.end_opt
        allow_2x_run = waypoint.speed in ['2x_run']
        allow_straight_run = waypoint.speed in ['2x_run', 'straight_run']
        allow_run = waypoint.speed in ['2x_run', 'straight_run', 'run']
        allow_rotation_set = True
        last_rotation = 0

        direction_interval = Timer(0.5, count=1)
        rotation_interval = Timer(0.3, count=1)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # Update
            self.minimap.update(self.device.image)

            # Arrive
            if self.minimap.is_position_near(waypoint.position, threshold=waypoint.get_threshold(end_opt)):
                logger.info(f'Arrive {waypoint}')
                break

            # Switch run case
            diff = self.minimap.position_diff(waypoint.position)
            if end_opt:
                if allow_2x_run and diff < 20:
                    logger.info(f'Approaching target, diff={round(diff, 1)}, disallow 2x_run')
                    allow_2x_run = False
                if allow_straight_run and diff < 15:
                    logger.info(f'Approaching target, diff={round(diff, 1)}, disallow straight_run')
                    direction_interval = Timer(0.2)
                    self.map_2x_run_timer.reset()
                    allow_straight_run = False
                if allow_run and diff < 7:
                    logger.info(f'Approaching target, diff={round(diff, 1)}, disallow run')
                    direction_interval = Timer(0.2)
                    allow_run = False

            # Control
            direction = self.minimap.position2direction(waypoint.position)
            if allow_2x_run:
                # Run with 2x_run button
                # - Set rotation once
                # - Continuous fine-tuning direction
                # - Enable 2x_run
                if allow_rotation_set:
                    # Cache rotation cause rotation detection has a higher error rate
                    last_rotation = self.minimap.rotation
                    if self.minimap.is_rotation_near(direction, threshold=10):
                        logger.info(f'Already at target rotation, '
                                    f'current={last_rotation}, target={direction}, disallow rotation_set')
                        allow_rotation_set = False
                if allow_rotation_set and rotation_interval.reached():
                    if self.handle_rotation_set(direction, threshold=10):
                        rotation_interval.reset()
                        direction_interval.reset()
                if direction_interval.reached():
                    contact.set(direction=diff_to_180_180(direction - last_rotation), run=True)
                    direction_interval.reset()
                self.handle_map_2x_run(run=True)
            elif allow_straight_run:
                # Run straight forward
                # - Set rotation once
                # - Continuous fine-tuning direction
                # - Disable 2x_run
                if allow_rotation_set:
                    # Cache rotation cause rotation detection has a higher error rate
                    last_rotation = self.minimap.rotation
                    if self.minimap.is_rotation_near(direction, threshold=10):
                        logger.info(f'Already at target rotation, '
                                    f'current={last_rotation}, target={direction}, disallow rotation_set')
                        allow_rotation_set = False
                if allow_rotation_set and rotation_interval.reached():
                    if self.handle_rotation_set(direction, threshold=10):
                        rotation_interval.reset()
                        direction_interval.reset()
                if direction_interval.reached():
                    contact.set(direction=diff_to_180_180(direction - last_rotation), run=True)
                    direction_interval.reset()
                self.handle_map_2x_run(run=False)
            elif allow_run:
                # Run
                # - No rotation set
                # - Continuous fine-tuning direction
                # - Disable 2x_run
                if allow_rotation_set:
                    last_rotation = self.minimap.rotation
                    allow_rotation_set = False
                if direction_interval.reached():
                    contact.set(direction=diff_to_180_180(direction - last_rotation), run=True)
                self.handle_map_2x_run(run=False)
            else:
                # Walk
                # - Continuous fine-tuning direction
                # - Disable 2x_run
                if allow_rotation_set:
                    last_rotation = self.minimap.rotation
                    allow_rotation_set = False
                if direction_interval.reached():
                    contact.set(direction=diff_to_180_180(direction - last_rotation), run=False)
                    direction_interval.reset()
                self.handle_map_2x_run(run=False)

    def goto(
            self,
            *waypoints,
            skip_first_screenshot=True
    ):
        """
        Go along a list of position, or goto target position

        Args:
            waypoints:
                position (x, y) to goto, or a list of position to go along.
                Waypoint object to goto, or a list of Waypoint objects to go along.

            skip_first_screenshot:
        """
        logger.hr('Goto', level=1)
        waypoints = [ensure_waypoint(point) for point in waypoints]
        logger.info(f'Go along {len(waypoints)} waypoints')
        end_list = [False for _ in waypoints]
        end_list[-1] = True

        with JoystickContact(self) as contact:
            for point, end in zip(waypoints, end_list):
                point: Waypoint
                self._goto(
                    contact=contact,
                    waypoint=point,
                    end_opt=end,
                    skip_first_screenshot=skip_first_screenshot
                )
                skip_first_screenshot = True

        end_point = waypoints[-1]
        if end_point.end_rotation is not None:
            logger.hr('End rotation', level=1)
            self.rotation_set(end_point.end_rotation, threshold=end_point.end_rotation_threshold)


if __name__ == '__main__':
    # Control test in Himeko trial
    # Must manually enter Himeko trial first and dismiss popup
    self = MapControl('src')
    self.minimap.set_plane('Jarilo_BackwaterPass', floor='F1')
    self.device.screenshot()
    self.minimap.init_position((519, 359))
    # Visit 3 items
    self.goto(
        Waypoint((577.6, 363.4)),
    )
    self.goto(
        Waypoint((577.5, 369.4), end_rotation=200),
    )
    self.goto(
        Waypoint((581.5, 387.3)),
        Waypoint((577.4, 411.5)),
    )
    # Goto boss
    self.goto(
        Waypoint((607.6, 425.3)),
    )
