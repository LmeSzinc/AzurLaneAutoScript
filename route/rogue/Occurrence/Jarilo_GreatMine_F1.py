from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_GreatMine
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_GreatMine_F1_X153Y271(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((153.8, 271.7)), | 79.8      | 75       |
        | event    | Waypoint((198.5, 257.0)), | 87.9      | 82       |
        | exit     | Waypoint((198.5, 258.5)), | 342.3     | 80       |
        """
        self.map_init(plane=Jarilo_GreatMine, floor="F1", position=(153.8, 271.7))
        self.register_domain_exit(Waypoint((198.5, 258.5)), end_rotation=80)
        event = Waypoint((198.5, 257.0))

        self.clear_event(event)
        # ===== End of generated waypoints =====
