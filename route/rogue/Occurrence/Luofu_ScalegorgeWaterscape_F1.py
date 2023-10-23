from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_ScalegorgeWaterscape
from tasks.map.route.base import locked_rotation
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_ScalegorgeWaterscape_F1_X499Y135(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((499.5, 135.3)), | 190.1     | 184      |
        | event    | Waypoint((942.8, 291.1)), | 193.0     | 186      |
        | exit     | Waypoint((499.2, 169.4)), | 187.1     | 179      |
        """
        self.map_init(plane=Luofu_ScalegorgeWaterscape, floor="F1", position=(499.5, 135.3))
        self.register_domain_exit(Waypoint((499.2, 169.4)), end_rotation=179)
        event = Waypoint((942.8, 291.1))

        self.clear_event(event)
        # ===== End of generated waypoints =====

    @locked_rotation(180)
    def Luofu_ScalegorgeWaterscape_F1_X619Y387(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((619.4, 387.3)), | 190.1     | 184      |
        | item     | Waypoint((626.2, 408.2)), | 157.2     | 151      |
        | event    | Waypoint((622.3, 422.5)), | 190.1     | 186      |
        | exit     | Waypoint((619.0, 423.6)), | 190.1     | 184      |
        """
        self.map_init(plane=Luofu_ScalegorgeWaterscape, floor="F1", position=(619.4, 387.3))
        self.register_domain_exit(Waypoint((619.0, 423.6)), end_rotation=184)
        item = Waypoint((626.2, 408.2))
        event = Waypoint((622.3, 422.5))

        self.clear_item(item)
        self.clear_event(event)
        # ===== End of generated waypoints =====

    def Luofu_ScalegorgeWaterscape_F1_X714Y243(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((714.4, 243.2)), | 274.2     | 274      |
        | event    | Waypoint((678.9, 243.0)), | 274.2     | 274      |
        | item     | Waypoint((323.2, 268.8)), | 302.6     | 297      |
        | exit     | Waypoint((677.4, 243.2)), | 274.2     | 271      |
        """
        self.map_init(plane=Luofu_ScalegorgeWaterscape, floor="F1", position=(714.4, 243.2))
        self.register_domain_exit(Waypoint((677.4, 243.2)), end_rotation=271)
        event = Waypoint((678.9, 243.0))
        item = Waypoint((323.2, 268.8))

        self.clear_item(item)
        self.clear_event(event)
        # ===== End of generated waypoints =====
