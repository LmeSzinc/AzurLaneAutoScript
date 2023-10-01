from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_GreatMine
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_GreatMine_F1_X494Y237(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((494.5, 237.2)), | 260.2     | 255      |
        | item     | Waypoint((476.4, 232.8)), | 289.0     | 288      |
        | herta    | Waypoint((444.4, 246.0)), | 250.8     | 253      |
        | exit     | Waypoint((435.4, 259.4)), | 241.3     | 239      |
        """
        self.map_init(plane=Jarilo_GreatMine, floor="F1", position=(494.5, 237.2))
        item = Waypoint((476.4, 232.8))
        herta = Waypoint((444.4, 246.0))
        exit_ = Waypoint((435.4, 259.4))

        self.clear_item(item)
        self.domain_herta(herta)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====
