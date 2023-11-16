from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_AlchemyCommission
from tasks.map.route.base import locked_position
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_AlchemyCommission_F2_X625Y590(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((623.1, 590.0)), | 282.2     | 274      |
        | enemy    | Waypoint((571.6, 589.5)), | 282.0     | 274      |
        | reward   | Waypoint((563.5, 581.4)), | 281.9     | 274      |
        | exit_    | Waypoint((555.5, 597.3)), | 267.8     | 264      |
        """
        self.map_init(plane=Luofu_AlchemyCommission, floor="F2", position=(623.1, 590.0))
        enemy = Waypoint((571.6, 589.5))
        reward = Waypoint((563.5, 581.4))
        exit_ = Waypoint((555.5, 597.3))

        self.clear_elite(enemy)
        self.domain_reward(reward)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====
