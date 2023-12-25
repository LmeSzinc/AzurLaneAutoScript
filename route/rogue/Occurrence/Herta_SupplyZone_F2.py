from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Herta_SupplyZone
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Herta_SupplyZone_F2_X45Y135(self):
        """
        | Waypoint | Position                 | Direction | Rotation |
        | -------- | ------------------------ | --------- | -------- |
        | spawn    | Waypoint((44.7, 134.6)), | 4.5       | 4        |
        | event    | Waypoint((49.4, 87.4)),  | 4.4       | 4        |
        | exit_    | Waypoint((47.2, 82.8)),  | 101.0     | 1        |
        | exit1    | Waypoint((43.3, 77.5)),  | 4.3       | 1        |
        | exit2    | Waypoint((51.4, 74.2)),  | 4.3       | 1        |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2", position=(44.7, 134.6))
        self.register_domain_exit(
            Waypoint((47.2, 82.8)), end_rotation=1,
            left_door=Waypoint((43.3, 77.5)), right_door=Waypoint((51.4, 74.2)))
        event = Waypoint((49.4, 87.4))

        self.clear_event(event)
        # ===== End of generated waypoints =====
