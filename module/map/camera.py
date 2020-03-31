import numpy as np

from module.handler.info_bar import InfoBarHandler
from module.logger import logger
from module.map.grids import Grids, Grid
from module.map.map_base import CampaignMap, location2node, location_ensure

param_x = np.array([4.41071252e+00, -3.90656142e-03, 1.95849683e+02])
param_y_positive = np.array([4.88226475e+00, -2.79093133e-03, 1.39520005e+02])
param_y_negative = np.array([4.58377745e+00, 3.13441976e-04, 1.39028669e+02])


def swipe_multiply_1d(x, a, b, c):
    return a / (x + b) + c


def swipe_multiply_2d(x, y):
    if abs(x) > 0.3:
        x = swipe_multiply_1d(abs(x), *param_x) * x
    else:
        x = x * 200

    if abs(y) > 0.3:
        y = swipe_multiply_1d(y, *param_y_positive) * y if y > 0 else swipe_multiply_1d(-y, *param_y_negative) * y
    else:
        y = y * 140

    return x, y


class Camera(InfoBarHandler):
    map: CampaignMap
    camera = (0, 0)

    def _map_swipe(self, vector, drop_threshold=0.1):
        """
        Args:
            vector(tuple, np.ndarray): float
            drop_threshold(float): swipe distance lower than this will be drop, because a closing swipe will be treat
                as a click in game.
        Returns:
            bool: if camera moved.
        """
        x, y = vector
        if abs(x) > drop_threshold or abs(y) > drop_threshold:
            # Linear fit
            # x = x * 200
            # y = y * 140
            # Function fit
            x, y = swipe_multiply_2d(x, y)

            vector = (-x, -y)
            self.device.swipe(vector)
            self.device.sleep(0.3)
            self.update()
        else:
            self.update(camera=False)

    def map_swipe(self, vector):
        """
        Swipe to a grid using relative position.
        Remember to update before calling this.

        Args:
            vector(tuple): int
        Returns:
            bool: if camera moved.
        """
        logger.info('Map swipe: %s' % str(vector))
        vector = np.array(vector)
        self.camera = tuple(vector + self.camera)
        vector = np.array([0.5, 0.5]) - np.array(self.grids.center_offset) + vector
        self._map_swipe(vector)

    def update(self, camera=True):
        """Update map image

        Args:
            camera: True to update camera position and perspective data.
        """
        self.device.screenshot()
        if not camera:
            self.grids.update(image=self.device.image)
            return True

        self.grids = Grids(self.device.image, config=self.config)

        # Catch perspective error
        known_exception = self.info_bar_count()
        if len(self.grids.horizontal) > self.map.shape[1] + 2 or len(self.grids.vertical) > self.map.shape[0] + 2:
            if not known_exception:
                logger.warn('Perspective Error. Too many lines')
            self.grids.correct = False
        if len(self.grids.horizontal) <= 3 or len(self.grids.vertical) <= 3:
            if not known_exception:
                logger.warn('Perspective Error. Too few lines')
            self.grids.correct = False

        if not self.grids.correct:
            if self.info_bar_count():
                logger.info('Perspective error cause by info bar. Waiting.')
                self.handle_info_bar()
                return self.update(camera=camera)
            else:
                self.grids.save_error_image()

        # Set camera position

        if self.grids.left_edge:
            x = 0 + self.grids.center_grid[0]
        elif self.grids.right_edge:
            x = self.map.shape[0] - self.grids.shape[0] + self.grids.center_grid[0]
        else:
            x = self.camera[0]
        if self.grids.lower_edge:
            y = 0 + self.grids.center_grid[1]
        elif self.grids.upper_edge:
            y = self.map.shape[1] - self.grids.shape[1] + self.grids.center_grid[1]
        else:
            y = self.camera[1]
        self.camera = (x, y)

        # align_x = self.map.shape[0] - self.grids.shape[0] if self.grids.right_edge else 0
        # align_y = self.map.shape[1] - self.grids.shape[1] if self.grids.upper_edge else 0
        # self.camera = np.array((align_x, align_y)) + self.grids.center_grid
        self.show_camera()

    def predict(self):
        self.grids.predict()
        self.map.update(grids=self.grids, camera=self.camera)

    def show_camera(self):
        logger.info('                Camera: %s' % location2node(self.camera))

    def ensure_edge_insight(self, reverse=False, preset=None):
        """
        Swipe to bottom left until two edges insight.
        Edges are used to locate camera.

        Args:
            reverse (bool): Reverse swipes.
            preset (tuple(int)): Set in map swipe manually.

        Returns:
            list[tuple]: Swipe record.
        """
        logger.info('Ensure edge in sight.')
        record = []
        self.update()

        if preset is not None:
            self.map_swipe(preset)
            record.append(preset)
            self.update()

        while 1:
            x = 0 if self.grids.left_edge or self.grids.right_edge else 3
            y = 0 if self.grids.lower_edge or self.grids.upper_edge else 2

            # Swipe even if two edges insight, this will avoid some embarrassing camera position.
            self.map_swipe((x, y))
            record.append((x, y))

            if x == 0 and y == 0:
                break

        if reverse:
            logger.info('Reverse swipes.')
            for vector in record[::-1]:
                x, y = vector
                if x != 0 and y != 0:
                    self.map_swipe((-x, -y))

        return record

    def focus_to(self, location, swipe_limit=(3, 2)):
        """Focus camera on a grid

        Args:
            location: grid
            swipe_limit(tuple): (x, y). Limit swipe in (-x, -y, x, y).
        """
        location = location_ensure(location)
        logger.info('Focus to: %s' % location2node(location))

        vector = np.array(location) - self.camera
        vector, sign = np.abs(vector), np.sign(vector)
        while 1:

            swipe = (
                vector[0] if vector[0] < swipe_limit[0] else swipe_limit[0],
                vector[1] if vector[1] < swipe_limit[1] else swipe_limit[1]
            )
            self.map_swipe(tuple(sign * swipe))

            vector -= swipe
            if np.all(np.abs(vector) <= 0):
                break

    def full_scan(self, battle_count=None, mystery_count=0, siren_count=0):
        """Scan the hole map.

        Args:
            battle_count:
            mystery_count:
        """
        logger.info('Full scan start')

        queue = self.map.camera_data
        while len(queue) > 0:
            if self.map.missing_is_none(battle_count, mystery_count, siren_count):
                logger.info('All spawn found, Early stopped.')
                break
            queue = queue.sort_by_camera_distance(self.camera)
            self.focus_to(queue[0])
            self.predict()
            queue = queue[1:]

        if battle_count is not None:
            self.map.missing_predict(battle_count=battle_count, mystery_count=mystery_count, siren_count=siren_count)
        self.map.show()

    def in_sight(self, location, sight=(-3, -1, 3, 2)):
        """Make sure location in camera sight

        Args:
            location:
            sight:
        """
        location = location_ensure(location)
        logger.info('In sight: %s' % location2node(location))

        diff = np.array(location) - self.camera
        if diff[1] > sight[3]:
            y = diff[1] - sight[3]
        elif diff[1] < sight[1]:
            y = diff[1] - sight[1]
        else:
            y = 0
        if diff[0] > sight[2]:
            x = diff[0] - sight[2]
        elif diff[0] < sight[0]:
            x = diff[0] - sight[0]
        else:
            x = 0
        self.focus_to((self.camera[0] + x, self.camera[1] + y))

    def convert_map_to_grid(self, location):
        """If self.grids doesn't contain this location, focus camera on the location and re-convert it.

        Args:
            location: Grid instance in self.map.

        Returns:
            Grid: Grid instance in self.grids.
        """
        location = location_ensure(location)

        grid = np.array(location) - self.camera + self.grids.center_grid
        logger.info('Convert_map_to_grid. Map: %s, Camera: %s, grids_center: %s, grid: %s' % (
            location2node(location), str(self.camera), str(self.grids.center_grid), str(grid)))
        if grid in self.grids:
            return self.grids[grid]
        else:
            logger.warning('Convert_map_to_grid Failed. Map: %s, Camera: %s, grids_center: %s, grid: %s' % (
                location2node(location), str(self.camera), str(self.grids.center_grid), str(grid)))
            self.grids.save_error_image()
            self.focus_to(location)
            grid = np.array(location) - self.camera + self.grids.center_grid
            return self.grids[grid]

    def full_scan_find_boss(self):
        logger.info('Full scan find boss.')
        queue = self.map.select(may_boss=True)
        while len(queue) > 0:
            queue = queue.sort_by_camera_distance(self.camera)
            self.in_sight(queue[0])
            self.predict()
            queue = queue[1:]

            boss = self.map.select(is_boss=True)
            boss = boss.add(self.map.select(may_boss=True, is_enemy=True))
            if boss:
                logger.info(f'Boss found: {boss}')
                self.map.show()
                return True

        logger.warning('No boss found.')
        return False
