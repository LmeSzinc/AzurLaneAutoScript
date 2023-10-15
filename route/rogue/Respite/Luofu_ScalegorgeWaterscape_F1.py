from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_ScalegorgeWaterscape
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def map_init(self, *args, **kwargs):
        super().map_init(*args, **kwargs)
        self.minimap.init_position(self.minimap.position, locked=True)

    def Luofu_ScalegorgeWaterscape_F1_X701Y321(self):
        """
        | Waypoint      | Position                  | Direction | Rotation |
        | ------------- | ------------------------- | --------- | -------- |
        | spawn         | Waypoint((701.5, 320.8)), | 274.2     | 274      |
        | item_X691Y314 | Waypoint((691.4, 314.9)), | 315.9     | 301      |
        | herta         | Waypoint((673.0, 314.9)), | 300.1     | 297      |
        | exit_X664Y319 | Waypoint((664.2, 319.4)), | 256.9     | 264      |
        """
        self.map_init(plane=Luofu_ScalegorgeWaterscape, floor="F1", position=(701.5, 320.8))
        item_X691Y314 = Waypoint((691.4, 314.9))
        herta = Waypoint((673.0, 314.9))
        exit_X664Y319 = Waypoint((664.2, 319.4))

        self.clear_item(item_X691Y314)
        self.domain_herta(herta)
        self.domain_single_exit(exit_X664Y319)
        # ===== End of generated waypoints =====
