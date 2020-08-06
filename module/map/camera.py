import numpy as np

from module.exception import MapDetectionError
from module.handler.assets import IN_MAP
from module.handler.info_handler import InfoHandler
from module.logger import logger
from module.map.map_base import CampaignMap, location2node, location_ensure
from module.map_detection.grid import Grid
from module.map_detection.view import View


class Camera(InfoHandler):
    view: View
    map: CampaignMap
    camera = (0, 0)

    def _map_swipe(self, vector):
        """
        Args:
            vector(tuple, np.ndarray): float

        Returns:
            bool: if camera moved.
        """
        vector = np.array(vector)
        name = 'MAP_SWIPE_' + '_'.join([str(int(round(x))) for x in vector])
        if np.any(np.abs(vector) > self.config.MAP_SWIPE_DROP):
            # Map grid fit
            distance = self.view.swipe_base * self.config.MAP_SWIPE_MULTIPLY
            vector = distance * vector

            vector = -vector
            self.device.swipe(vector, name=name)
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
        vector = np.array([0.5, 0.5]) - self.view.center_offset + vector
        self._map_swipe(vector)

    def focus_to_grid_center(self):
        """
        Re-focus to the center of a grid.

        Returns:
            bool: Map swiped.
        """
        if np.any(np.abs(self.view.center_offset - 0.5) > self.config.MAP_GRID_CENTER_TOLERANCE):
            logger.info('Re-focus to grid center.')
            self.map_swipe((0, 0))
            return True

        return False

    def update(self, camera=True):
        """Update map image

        Args:
            camera: True to update camera position and perspective data.
        """
        self.device.screenshot()
        if not camera:
            self.view.update(image=self.device.image)
            return True

        if not hasattr(self, 'view'):
            self.view = View(self.config)
        try:
            self.view.load(self.device.image)
        except MapDetectionError as e:
            if self.info_bar_count():
                logger.info('Perspective error cause by info bar. Waiting.')
                self.handle_info_bar()
                return self.update(camera=camera)
            elif not self.appear(IN_MAP):
                logger.warning('Image to detect is not in_map')
                raise e
            elif 'Camera outside map' in str(e):
                string = str(e)
                logger.warning(string)
                x, y = string.split('=')[1].strip('() ').split(',')
                self._map_swipe((-int(x.strip()), -int(y.strip())))
            else:
                raise e

        # Set camera position
        if self.view.left_edge:
            x = 0 + self.view.center_loca[0]
        elif self.view.right_edge:
            x = self.map.shape[0] - self.view.shape[0] + self.view.center_loca[0]
        else:
            x = self.camera[0]
        if self.view.lower_edge:
            y = 0 + self.view.center_loca[1]
        elif self.view.upper_edge:
            y = self.map.shape[1] - self.view.shape[1] + self.view.center_loca[1]
        else:
            y = self.camera[1]

        if self.camera != (x, y):
            logger.attr_align('camera_corrected', f'{location2node(self.camera)} -> {location2node((x, y))}')
        self.camera = (x, y)
        self.show_camera()

    def predict(self, mode='normal'):
        self.view.predict()
        self.map.update(grids=self.view, camera=self.camera, mode=mode)

    def show_camera(self):
        logger.attr_align('Camera', location2node(self.camera))

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

        while 1:
            if len(record) == 0:
                self.update()
                if preset is not None:
                    self.map_swipe(preset)
                    record.append(preset)

            x = 0 if self.view.left_edge or self.view.right_edge else 3
            y = 0 if self.view.lower_edge or self.view.upper_edge else 2

            if len(record) > 0:
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


    def full_scan(self, queue=None, must_scan=None, battle_count=0, mystery_count=0, siren_count=0, carrier_count=0,
                  mode='normal'):
        """Scan the whole map.

        Args:
            queue (SelectedGrids): Grids to focus on. If none, use map.camera_data
            must_scan (SelectedGrids): Must scan these grids
            battle_count:
            mystery_count:
            siren_count:
            carrier_count:
            mode (str): Scan mode, such as 'normal', 'carrier', 'movable'

        """
        logger.info('Full scan start')
        self.map.reset_fleet()

        queue = queue if queue else self.map.camera_data
        if must_scan:
            queue = queue.add(must_scan)

        while len(queue) > 0:
            if self.map.missing_is_none(battle_count, mystery_count, siren_count, carrier_count):
                if must_scan and queue.count != queue.delete(must_scan).count:
                    logger.info('Continue scanning.')
                    pass
                else:
                    logger.info('All spawn found, Early stopped.')
                    break

            queue = queue.sort_by_camera_distance(self.camera)
            self.focus_to(queue[0])
            self.view.predict()
            success = self.map.update(grids=self.view, camera=self.camera, mode=mode)
            if not success:
                self.ensure_edge_insight()
                continue

            queue = queue[1:]

        self.map.missing_predict(battle_count, mystery_count, siren_count, carrier_count)


        self.map.show()

    def in_sight(self, location, sight=None):
        """Make sure location in camera sight

        Args:
            location:
            sight (tuple): Such as (-3, -1, 3, 2).
        """
        location = location_ensure(location)
        logger.info('In sight: %s' % location2node(location))
        if sight is None:
            sight = self.map.camera_sight

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

        local = np.array(location) - self.camera + self.view.center_loca
        logger.info('Global %s (camera=%s) -> Local %s (center=%s)' % (
            location2node(location),
            location2node(self.camera),
            location2node(local),
            location2node(self.view.center_loca)
        ))
        if local in self.view:
            return self.view[local]
        else:
            logger.warning('Convert global to local Failed.')
            self.focus_to(location)
            local = np.array(location) - self.camera + self.view.center_loca
            return self.view[local]

    def full_scan_find_boss(self):
        logger.info('Full scan find boss.')
        self.map.reset_fleet()

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
