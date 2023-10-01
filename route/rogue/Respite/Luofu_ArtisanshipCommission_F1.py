from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_ArtisanshipCommission
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_ArtisanshipCommission_F1_X299Y863(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((299.6, 863.4)), | 6.7       | 4        |
        | item     | Waypoint((306.8, 850.6)), | 33.9      | 31       |
        | herta    | Waypoint((305.2, 821.0)), | 11.2      | 8        |
        | exit     | Waypoint((301.0, 808.4)), | 2.7       | 357      |
        """
        self.map_init(plane=Luofu_ArtisanshipCommission, floor="F1", position=(299.6, 863.4))
        item = Waypoint((306.8, 850.6))
        herta = Waypoint((305.2, 821.0))
        exit_ = Waypoint((301.0, 808.4))

        self.clear_item(item)
        self.domain_herta(herta)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====
