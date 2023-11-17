from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_DivinationCommission
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_DivinationCommission_F2_X216Y659(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((216.8, 659.5)), | 281.9     | 274      |
        | enemy    | Waypoint((164.0, 660.2)), | 275.8     | 271      |
        | exit_    | Waypoint((164.0, 660.2)), | 275.8     | 271      |
        | exit1    | Waypoint((153.8, 670.7)), | 277.1     | 271      |
        | exit2    | Waypoint((153.5, 651.6)), | 277.2     | 274      |
        """
        self.map_init(plane=Luofu_DivinationCommission, floor="F2", position=(216.8, 659.5))
        self.register_domain_exit(
            Waypoint((164.0, 660.2)), end_rotation=271,
            left_door=Waypoint((153.8, 670.7)), right_door=Waypoint((153.5, 651.6)))
        enemy = Waypoint((164.0, 660.2))
        # ===== End of generated waypoints =====

        self.clear_enemy(enemy)

    def Luofu_DivinationCommission_F2_X239Y785(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((239.4, 785.5)), | 282.2     | 274      |
        | enemy    | Waypoint((188.9, 784.2)), | 281.9     | 274      |
        | exit_    | Waypoint((189.4, 784.2)), | 182.7     | 269      |
        | exit1    | Waypoint((179.0, 794.9)), | 272.8     | 269      |
        | exit2    | Waypoint((179.6, 775.4)), | 272.8     | 269      |
        """
        self.map_init(plane=Luofu_DivinationCommission, floor="F2", position=(239.4, 785.5))
        self.register_domain_exit(
            Waypoint((189.4, 784.2)), end_rotation=269,
            left_door=Waypoint((179.0, 794.9)), right_door=Waypoint((179.6, 775.4)))
        enemy = Waypoint((188.9, 784.2))
        # ===== End of generated waypoints =====

        self.clear_enemy(enemy)
