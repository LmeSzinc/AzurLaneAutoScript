from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_AlchemyCommission
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_AlchemyCommission_F1_X301Y441(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((301.6, 441.5)), | 282.2     | 274      |
        | enemy    | Waypoint((248.6, 441.0)), | 282.0     | 274      |
        | exit_    | Waypoint((248.6, 441.0)), | 282.0     | 274      |
        | exit1    | Waypoint((235.8, 448.9)), | 282.0     | 274      |
        | exit2    | Waypoint((239.4, 432.2)), | 282.1     | 274      |
        """
        self.map_init(plane=Luofu_AlchemyCommission, floor="F1", position=(301.6, 441.5))
        self.register_domain_exit(
            Waypoint((248.6, 441.0)), end_rotation=274,
            left_door=Waypoint((235.8, 448.9)), right_door=Waypoint((239.4, 432.2)))
        enemy = Waypoint((248.6, 441.0))
        # ===== End of generated waypoints =====

        self.clear_enemy(enemy)
