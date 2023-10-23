from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_Cloudford
from tasks.map.route.base import locked_rotation
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    @locked_rotation(0)
    def Luofu_Cloudford_F1_X337Y1003(self):
        """
        | Waypoint | Position                   | Direction | Rotation |
        | -------- | -------------------------- | --------- | -------- |
        | spawn    | Waypoint((337.3, 1003.4)), | 6.7       | 4        |
        | enemy    | Waypoint((336.2, 962.2)),  | 6.7       | 4        |
        | reward   | Waypoint((342.9, 954.8)),  | 44.2      | 31       |
        | exit     | Waypoint((328.8, 942.8)),  | 316.1     | 331      |
        """
        self.map_init(plane=Luofu_Cloudford, floor="F1", position=(337.3, 1003.4))
        enemy = Waypoint((336.2, 962.2))
        reward = Waypoint((342.9, 954.8))
        exit_ = Waypoint((328.8, 942.8))

        self.clear_elite(enemy)
        self.domain_reward(reward)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====
