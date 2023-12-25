from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_DivinationCommission
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_DivinationCommission_F2_X824Y659(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((824.7, 659.4)), | 94.2      | 91       |
        | item     | Waypoint((838.0, 666.8)), | 149.5     | 91       |
        | herta    | Waypoint((868.0, 667.2)), | 101.1     | 98       |
        | exit_    | Waypoint((881.4, 659.4)), | 101.2     | 98       |
        """
        self.map_init(plane=Luofu_DivinationCommission, floor="F2", position=(824.7, 659.4))
        item = Waypoint((838.0, 666.8))
        herta = Waypoint((868.0, 667.2))
        exit_ = Waypoint((881.4, 659.4))

        self.clear_item(item)
        self.domain_herta(herta)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====
