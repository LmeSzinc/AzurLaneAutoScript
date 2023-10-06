from collections import deque
from functools import cached_property

import numpy as np

from module.base.timer import Timer
from module.logger import logger
from tasks.base.assets.assets_base_page import CLOSE
from tasks.combat.combat import Combat
from tasks.map.assets.assets_map_control import ROTATION_SWIPE_AREA
from tasks.map.control.joystick import JoystickContact
from tasks.map.control.waypoint import Waypoint, ensure_waypoints
from tasks.map.interact.aim import AimDetectorMixin
from tasks.map.minimap.minimap import Minimap
from tasks.map.resource.const import diff_to_180_180


class MapControl(Combat, AimDetectorMixin):
    waypoint: Waypoint

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

    def walk_additional(self) -> bool:
        """
        Handle popups during walk

        Returns:
            bool: If handled
        """
        if self.appear_then_click(CLOSE):
            return True

        return False

    def _goto(
            self,
            contact: JoystickContact,
            waypoint: Waypoint,
            end_opt=True,
            skip_first_screenshot=False
    ) -> list[str]:
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

        Returns:
            list[str]: A list of walk result
        """
        logger.hr('Goto', level=2)
        logger.info(f'Goto {waypoint}')
        self.waypoint = waypoint
        self.device.stuck_record_clear()
        self.device.click_record_clear()

        end_opt = end_opt and waypoint.end_opt
        allow_run_2x = waypoint.speed in ['run_2x']
        allow_straight_run = waypoint.speed in ['run_2x', 'straight_run']
        allow_run = waypoint.speed in ['run_2x', 'straight_run', 'run']
        allow_walk = True
        allow_rotation_set = True
        last_rotation = 0

        result = []

        direction_interval = Timer(0.5, count=1)
        rotation_interval = Timer(0.3, count=1)
        aim_interval = Timer(0.3, count=1)
        attacked_enemy = Timer(1.2, count=4)
        attacked_item = Timer(0.6, count=2)
        near_queue = deque(maxlen=waypoint.unexpected_confirm.count)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            for expected in waypoint.expected_end:
                if callable(expected):
                    if expected():
                        logger.info(f'Walk result add: {expected.__name__}')
                        result.append(expected.__name__)
                        return result
            if self.is_combat_executing():
                logger.info('Walk result add: enemy')
                result.append('enemy')
                contact.up()
                logger.hr('Combat', level=2)
                self.combat_execute()
                if waypoint.early_stop:
                    return result
            if self.walk_additional():
                attacked_enemy.clear()
                attacked_item.clear()
                continue

            # The following detection require page_main
            if not self.is_in_main():
                attacked_enemy.clear()
                attacked_item.clear()
                continue

            # Update
            self.minimap.update(self.device.image)
            if aim_interval.reached_and_reset():
                self.aim.predict(self.device.image)
            diff = self.minimap.position_diff(waypoint.position)
            direction = self.minimap.position2direction(waypoint.position)
            rotation_diff = self.minimap.rotation_diff(direction)
            logger.info(f'Pdiff: {diff}, Ddiff: {direction}, Rdiff: {rotation_diff}')

            def contact_direction():
                if waypoint.lock_direction is not None:
                    return waypoint.lock_direction
                return diff_to_180_180(direction - last_rotation)

            # Interact
            if self.aim.aimed_enemy:
                if 'enemy' in waypoint.expected_end:
                    if self.handle_map_A():
                        allow_run_2x = allow_straight_run = False
                        attacked_enemy.reset()
                        direction_interval.reset()
                        rotation_interval.reset()
                if attacked_enemy.started():
                    attacked_enemy.reset()
            if self.aim.aimed_item:
                if 'item' in waypoint.expected_end:
                    if self.handle_map_A():
                        allow_run_2x = allow_straight_run = False
                        attacked_item.reset()
                        direction_interval.reset()
                        rotation_interval.reset()
                if attacked_item.started():
                    attacked_item.reset()
            else:
                if attacked_item.started() and attacked_item.reached():
                    logger.info('Walk result add: item')
                    result.append('item')
                    if waypoint.early_stop:
                        return result
            if waypoint.interact_radius > 0:
                if diff < waypoint.interact_radius:
                    self.handle_combat_interact()

            # Arrive
            if near := self.minimap.is_position_near(waypoint.position, threshold=waypoint.get_threshold(end_opt)):
                near_queue.append(near)
                if not waypoint.expected_end or waypoint.match_results(result):
                    logger.info(f'Arrive waypoint: {waypoint}')
                    return result
                else:
                    if waypoint.unexpected_confirm.reached():
                        logger.info(f'Arrive waypoint with unexpected result: {waypoint}')
                        return result
            else:
                near_queue.append(near)
                if np.mean(near_queue) < 0.6:
                    waypoint.unexpected_confirm.reset()

            # Switch run case
            if end_opt:
                if allow_run_2x and diff < 20:
                    logger.info(f'Approaching target, diff={round(diff, 1)}, disallow run_2x')
                    allow_run_2x = False
                if allow_straight_run and diff < 15 and not allow_rotation_set:
                    logger.info(f'Approaching target, diff={round(diff, 1)}, disallow straight_run')
                    direction_interval = Timer(0.2)
                    aim_interval = Timer(0.1)
                    self.map_run_2x_timer.reset()
                    allow_straight_run = False
                if allow_run and diff < 7 and waypoint.min_speed == 'walk':
                    logger.info(f'Approaching target, diff={round(diff, 1)}, disallow run')
                    direction_interval = Timer(0.2)
                    aim_interval = Timer(0.2)
                    allow_run = False

            # Control
            if allow_run_2x:
                # Run with run_2x button
                # - Set rotation once
                # - Continuous fine-tuning direction
                # - Enable run_2x
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
                    contact.set(direction=contact_direction(), run=True)
                    direction_interval.reset()
                self.handle_map_run_2x(run=True)
            elif allow_straight_run:
                # Run straight forward
                # - Set rotation once
                # - Continuous fine-tuning direction
                # - Disable run_2x
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
                    contact.set(direction=contact_direction(), run=True)
                    direction_interval.reset()
                self.handle_map_run_2x(run=False)
            elif allow_run:
                # Run
                # - No rotation set
                # - Continuous fine-tuning direction
                # - Disable run_2x
                if allow_rotation_set:
                    last_rotation = self.minimap.rotation
                    allow_rotation_set = False
                if direction_interval.reached():
                    contact.set(direction=contact_direction(), run=True)
                    direction_interval.reset()
                self.handle_map_run_2x(run=False)
            elif allow_walk:
                # Walk
                # - Continuous fine-tuning direction
                # - Disable run_2x
                if allow_rotation_set:
                    last_rotation = self.minimap.rotation
                    allow_rotation_set = False
                if direction_interval.reached():
                    contact.set(direction=contact_direction(), run=False)
                    direction_interval.reset()
                self.handle_map_run_2x(run=False)
            else:
                contact.up()

    def goto(self, *waypoints):
        """
        Go along a list of position, or goto target position.

        Args:
            waypoints: position (x, y), a list of position to go along,
                or a list of Waypoint objects to go along.

        Returns:
            list[str]: A list of walk result
        """
        logger.hr('Goto', level=1)
        self.map_A_timer.clear()
        self.map_E_timer.clear()
        self.map_run_2x_timer.clear()
        waypoints = ensure_waypoints(waypoints)
        logger.info(f'Go along {len(waypoints)} waypoints')
        end_list = [False for _ in waypoints]
        end_list[-1] = True

        results = []
        with JoystickContact(self) as contact:
            for waypoint, end in zip(waypoints, end_list):
                waypoint: Waypoint
                result = self._goto(
                    contact=contact,
                    waypoint=waypoint,
                    end_opt=end,
                    skip_first_screenshot=True,
                )
                expected = waypoint.expected_to_str(waypoint.expected_end)
                logger.info(f'Arrive waypoint, expected: {expected}, result: {result}')
                results += result
                matched = waypoint.match_results(result)
                if not waypoint.expected_end or matched:
                    logger.info(f'Arrive waypoint with expected result: {matched}')
                else:
                    logger.warning(f'Arrive waypoint with unexpected result: {result}')

        return results

    def clear_item(self, *waypoints):
        """
        Go along a list of position and clear destructive object at last.

        Args:
            waypoints: position (x, y), a list of position to go along.
                or a list of Waypoint objects to go along.
        """
        logger.hr('Clear item', level=1)
        waypoints = ensure_waypoints(waypoints)
        end_point = waypoints[-1]
        end_point.expected_end.append('item')

        self.goto(*waypoints)

    def clear_enemy(self, *waypoints):
        """
        Go along a list of position and enemy at last.

        Args:
            waypoints: position (x, y), a list of position to go along.
                or a list of Waypoint objects to go along.
        """
        logger.hr('Clear enemy', level=1)
        waypoints = ensure_waypoints(waypoints)
        end_point = waypoints[-1]
        end_point.expected_end.append('enemy')

        self.goto(*waypoints)


if __name__ == '__main__':
    # Control test in Himeko trial
    # Must manually enter Himeko trial first and dismiss popup
    self = MapControl('src')
    self.minimap.set_plane('Jarilo_BackwaterPass', floor='F1')
    self.device.screenshot()
    self.minimap.init_position((519, 359))
    # Visit 3 items
    self.clear_item(
        Waypoint((587.6, 366.9)).run_2x(),
    )
    self.clear_item(
        Waypoint((575.5, 377.4)).straight_run(),
    )
    self.clear_item(
        # Go through arched door
        Waypoint((581.5, 383.3)).set_threshold(3),
        Waypoint((575.7, 417.2)),
    )
    # Goto boss
    self.clear_enemy(
        Waypoint((613.5, 427.3)).straight_run(),
    )
