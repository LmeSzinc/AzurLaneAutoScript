from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_ScalegorgeWaterscape
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_ScalegorgeWaterscape_F1_X701Y321(self):
        """
        | Waypoint | Position                   | Direction | Rotation |
        | -------- | -------------------------- | --------- | -------- |
        | spawn    | Waypoint((701.5, 320.8)),  | 274.2     | 274      |
        | herta    | Waypoint((673.0, 314.9)),  | 300.1     | 297      |
        | item     | Waypoint((1418.8, 300.8)), | 315.9     | 301      |
        | exit     | Waypoint((953.0, 279.7)),  | 263.8     | 258      |
        """
        self.map_init(plane=Luofu_ScalegorgeWaterscape, floor="F1", position=(701.5, 320.8))
        herta = Waypoint((673.0, 314.9))
        item = Waypoint((1418.8, 300.8))
        exit_ = Waypoint((953.0, 279.7))

        self.clear_item(item)
        self.domain_herta(herta)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====
