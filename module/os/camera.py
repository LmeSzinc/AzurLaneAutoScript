import numpy as np

from module.base.decorator import cached_property
from module.exception import MapDetectionError
from module.logger import logger
from module.map.camera import Camera
from module.map.map_base import location2node, location_ensure
from module.map_detection.os_grid import OSGrid
from module.map_detection.view import View
from module.os.map_operation import OSMapOperation
from module.os.radar import Radar


class OSCamera(OSMapOperation, Camera):
    radar: Radar
    fleet_current: tuple

    def _map_swipe(self, vector, box=(239, 128, 993, 628)):
        return super()._map_swipe(vector, box=box)

    def _view_init(self):
        if not hasattr(self, "view"):
            storage = ((10, 7), [(110.307, 103.657), (1012.311, 103.657), (-32.959, 600.567), (1113.057, 600.567)])
            view = View(self.config, mode="os", grid_class=OSGrid)
            view.detector_set_backend("homography")
            view.backend.load_homography(storage=storage)
            self.view = view

    @cached_property
    def radar(self):
        """
        Returns:
            Radar:
        """
        return Radar(self.config)

    def predict_radar(self):
        """
        Scan radar and merge it into map
        """
        self.radar.predict(self.device.image)
        self.radar.show()


    # def ensure_edge_insight(self, reverse=False, preset=None, swipe_limit=(4, 3)):
    #     return super().ensure_edge_insight(reverse=reverse, preset=preset, swipe_limit=swipe_limit)
    #
    # def focus_to(self, location, swipe_limit=(4, 3)):
    #     return super().focus_to(location, swipe_limit=swipe_limit)


    def update_os(self):
        """
        Similar to `Camera.update()`, but for OPSI.
        """
        # self.device.screenshot()
        self._view_init()

        try:
            self.view.load(self.device.image)
        except (MapDetectionError, AttributeError) as e:
            logger.warning(e)
            logger.warning("Assuming camera is focused on grid center")

            def empty(*args, **kwargs):
                pass

            backup, self.view.backend.load = self.view.backend.load, empty
            self.view.backend.homo_loca = (53, 60)
            self.view.backend.left_edge = False
            self.view.backend.right_edge = False
            self.view.backend.lower_edge = False
            self.view.backend.upper_edge = False
            self.view.load(self.device.image)
            self.view.backend.load = backup

    def convert_radar_to_local(self, location):
        """
        Converts the coordinate on radar to the coordinate of local map view,
        also handles a rare game bug.

        Usually, OPSI camera focus on current fleet, which is (5, 4) in local view.
        The convert should be `local = view[np.add(radar, view.center_loca)]`
        However, Azur Lane may bugged, not focusing current.
        In this case, the convert should base on fleet position.

        Args:
            location: (x, y), Position on radar.

        Returns:
            OSGrid: Grid instance in self.view
        """
        location = location_ensure(location)

        fleets = self.view.select(is_current_fleet=True)
        if fleets.count == 1:
            center = fleets[0].location
        elif fleets.count > 1:
            logger.warning(f"Convert radar to local, but found multiple current fleets: {fleets}")
            fleets = fleets.sort_by_camera_distance(self.view.center_loca)
            center = fleets[0].location
            logger.warning(f"Assuming the nearest fleet to camera canter is current fleet: {location2node(center)}")
        else:
            logger.warning(
                f"Convert radar to local, but current fleet not found. "
                f"Assuming camera center is current fleet: {location2node(self.view.center_loca)}"
            )
            center = self.view.center_loca

        try:
            local = self.view[np.add(location, center)]
        except KeyError:
            logger.warning(
                f"Convert radar to local, but target grid not in local view. "
                f"Assuming camera center is current fleet: {location2node(self.view.center_loca)}"
            )
            center = self.view.center_loca
            local = self.view[np.add(location, center)]

        logger.info(
            "Radar %s -> Local %s (fleet=%s)" % (str(location), location2node(local.location), location2node(center))
        )
        return local
