from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_Cloudford
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_Cloudford_F1_X417Y933(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((417.5, 933.4)), | 96.7      | 91       |
        | item     | Waypoint((431.0, 940.6)), | 129.8     | 124      |
        | herta    | Waypoint((464.4, 942.4)), | 112.7     | 110      |
        | exit     | Waypoint((476.2, 934.2)), | 87.8      | 82       |
        """
        self.map_init(plane=Luofu_Cloudford, floor="F1", position=(417.5, 933.4))
        item = Waypoint((431.0, 940.6))
        herta = Waypoint((464.4, 942.4))
        exit_ = Waypoint((476.2, 934.2))

        self.clear_item(item)
        self.domain_herta(herta)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====
