import numpy as np

from module.logger import logger
from module.map.camera import Camera
from module.map.map_base import location_ensure
from module.map_detection.view import View
from module.os.radar import Radar
from module.os.map_operation import OSMapOperation


class OSCamera(OSMapOperation, Camera):
    radar: Radar
    fleet_current: tuple

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
            if self.config.DEVICE_CONTROL_METHOD == 'minitouch':
                distance = self.view.swipe_base * self.config.MAP_SWIPE_MULTIPLY_MINITOUCH
            else:
                distance = self.view.swipe_base * self.config.MAP_SWIPE_MULTIPLY
            vector = distance * vector

            vector = -vector
            self.device.swipe(vector, name=name, box=(234, 123, 998, 633))
            self.device.sleep(0.3)
            self.update()
        else:
            self.update(camera=False)

    def _view_init(self):
        if not hasattr(self, 'view'):
            self.view = View(self.config, mode='os')

    def update_radar(self):
        """
        Scan radar and merge it into map
        """
        if not hasattr(self, 'radar'):
            self.radar = Radar(self.config)
        self.radar.predict(self.device.image)
        self.map.update(self.radar, camera=self.fleet_current)

    def grid_is_in_sight(self, grid, camera=None, sight=None):
        location = location_ensure(grid)
        camera = location_ensure(camera) if camera is not None else self.camera
        if sight is None:
            sight = self.map.camera_sight

        diff = np.array(location) - camera
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
        return x == 0 and y == 0
