import numpy as np

from module.base.button import Button
from module.base.decorator import cached_property
from module.logger import logger
from module.map.camera import Camera
from module.map.map_base import location_ensure
from module.map_detection.view import View
from module.os.map_operation import OSMapOperation
from module.os.radar import Radar


class OSCamera(OSMapOperation, Camera):
    radar: Radar
    fleet_current: tuple

    def _map_swipe(self, vector, box=(234, 123, 998, 633)):
        return super()._map_swipe(vector, box=box)

    def _view_init(self):
        if not hasattr(self, 'view'):
            self.view = View(self.config, mode='os')

    @cached_property
    def radar(self):
        """
        Returns:
            Radar:
        """
        return Radar(self.config)

    def update_radar(self):
        """
        Scan radar and merge it into map
        """
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

    def _get_map_outside_button(self):
        """
        Returns:
            Button: Click outside of map.
        """
        for _ in range(2):
            if self.view.left_edge:
                edge = self.view.backend.left_edge
                area = (113, 185, edge.get_x(290), 290)
            elif self.view.right_edge:
                edge = self.view.backend.right_edge
                area = (edge.get_x(360), 360, 1280, 560)
            else:
                logger.info('No left edge or right edge')
                self.ensure_edge_insight()
                continue

            button = Button(area=area, color=(), button=area, name='MAP_OUTSIDE')
            return button

    @cached_property
    def os_default_view(self):
        """
        Returns:
            View:
        """
        def empty(*args, **kwargs):
            pass

        storage = ((10, 7), [(110.307, 103.657), (1012.311, 103.657), (-32.959, 600.567), (1113.057, 600.567)])
        view = View(self.config, mode='os')
        view.detector_set_backend('homography')
        view.backend.load_homography(storage=storage)
        view.backend.load = empty
        view.backend.left_edge = None
        view.backend.right_edge = None
        view.backend.upper_edge = None
        view.backend.lower_edge = None
        view.backend.homo_loca = (53, 60)
        view.load(self.device.image)

        return view
