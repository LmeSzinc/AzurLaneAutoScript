from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_SilvermaneGuardRestrictedZone
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_SilvermaneGuardRestrictedZone_F1_X777Y199(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((777.2, 199.7)), | 96.7      | 91       |
        | item     | Waypoint((790.8, 206.8)), | 129.8     | 126      |
        | herta    | Waypoint((822.8, 208.2)), | 101.2     | 96       |
        | exit     | Waypoint((834.6, 198.9)), | 102.7     | 96       |
        """
        self.map_init(plane=Jarilo_SilvermaneGuardRestrictedZone, floor="F1", position=(777.2, 199.7))
        item = Waypoint((790.8, 206.8))
        herta = Waypoint((822.8, 208.2))
        exit_ = Waypoint((834.6, 198.9))

        self.clear_item(item)
        self.domain_herta(herta)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====
