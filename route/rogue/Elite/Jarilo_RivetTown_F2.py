from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_RivetTown
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_RivetTown_F2_X189Y81(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((189.5, 81.9)),  | 231.7     | 228      |
        | enemy    | Waypoint((155.4, 119.5)), | 191.8     | 223      |
        | reward   | Waypoint((145.0, 122.4)), | 256.7     | 251      |
        | exit     | Waypoint((151.1, 134.2)), | 203.1     | 198      |
        """
        self.map_init(plane=Jarilo_RivetTown, floor="F2", position=(189.5, 81.9))
        enemy = Waypoint((155.4, 119.5))
        reward = Waypoint((145.0, 122.4))
        exit_ = Waypoint((151.1, 134.2))

        self.clear_elite(enemy)
        self.domain_reward(reward)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====
