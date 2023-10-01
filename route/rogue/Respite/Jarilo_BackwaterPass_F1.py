from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_BackwaterPass
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_BackwaterPass_F1_X581Y403(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((581.5, 403.5)), | 131.7     | 126      |
        | item     | Waypoint((586.8, 418.6)), | 172.7     | 165      |
        | herta    | Waypoint((606.6, 433.0)), | 143.8     | 140      |
        | exit     | Waypoint((618.6, 430.6)), | 116.7     | 114      |
        """
        self.map_init(plane=Jarilo_BackwaterPass, floor="F1", position=(581.5, 403.5))
        item = Waypoint((586.8, 418.6))
        herta = Waypoint((606.6, 433.0))
        exit_ = Waypoint((618.6, 430.6))

        self.clear_item(item)
        self.domain_herta(herta)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====
