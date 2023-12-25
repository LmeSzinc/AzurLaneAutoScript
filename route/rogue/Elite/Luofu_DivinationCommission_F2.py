from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_DivinationCommission
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_DivinationCommission_F2_X338Y345(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((338.0, 345.5)), | 4.5       | 4        |
        | enemy    | Waypoint((338.4, 278.2)), | 4.3       | 4        |
        | reward   | Waypoint((345.8, 267.2)), | 99.0      | 1        |
        | exit_    | Waypoint((331.2, 261.0)), | 352.8     | 348      |
        """
        self.map_init(plane=Luofu_DivinationCommission, floor="F2", position=(338.0, 345.5))
        enemy = Waypoint((338.4, 278.2))
        reward = Waypoint((345.8, 267.2))
        exit_ = Waypoint((331.2, 261.0))

        self.clear_elite(enemy)
        self.domain_reward(reward)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====
