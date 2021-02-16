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

    def _map_swipe(self, vector, box=(234, 123, 998, 633)):
        return super()._map_swipe(vector, box=box)

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

    # def ensure_edge_insight(self, reverse=False, preset=None, swipe_limit=(4, 3)):
    #     return super().ensure_edge_insight(reverse=reverse, preset=preset, swipe_limit=swipe_limit)
    #
    # def focus_to(self, location, swipe_limit=(4, 3)):
    #     return super().focus_to(location, swipe_limit=swipe_limit)
