from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_BackwaterPass
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_BackwaterPass_F1_X437Y101(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((437.5, 101.5)), | 96.7      | 91       |
        | item     | Waypoint((458.6, 92.2)),  | 67.2      | 57       |
        | event    | Waypoint((476.8, 108.9)), | 103.8     | 96       |
        | exit     | Waypoint((483.4, 105.3)), | 4.1       | 89       |
        """
        self.map_init(plane=Jarilo_BackwaterPass, floor="F1", position=(437.5, 101.5))
        self.register_domain_exit(Waypoint((483.4, 105.3)), end_rotation=89)
        item = Waypoint((458.6, 92.2))
        event = Waypoint((476.8, 108.9))

        self.clear_item(item)
        self.clear_event(event)
        # ===== End of generated waypoints =====

    def Jarilo_BackwaterPass_F1_X613Y755(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((613.3, 755.7)), | 319.8     | 318      |
        | item     | Waypoint((603.0, 734.6)), | 342.6     | 343      |
        | event    | Waypoint((586.8, 724.7)), | 318.0     | 315      |
        | exit     | Waypoint((568.6, 730.6)), | 274.2     | 271      |
        """
        self.map_init(plane=Jarilo_BackwaterPass, floor="F1", position=(613.3, 755.7))
        self.register_domain_exit(Waypoint((568.6, 730.6)), end_rotation=271)
        item = Waypoint((603.0, 734.6))
        event = Waypoint((586.8, 724.7))

        self.clear_item(item)
        self.clear_event(event)
        # ===== End of generated waypoints =====
