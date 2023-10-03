from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_SilvermaneGuardRestrictedZone
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_SilvermaneGuardRestrictedZone_F1_X225Y425(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((225.3, 425.9)), | 274.2     | 274      |
        | enemy    | Waypoint((170.4, 428.6)), | 282.9     | 278      |
        | reward   | Waypoint((166.7, 419.1)), | 289.0     | 288      |
        | exit     | Waypoint((159.6, 434.6)), | 282.9     | 278      |
        """
        self.map_init(plane=Jarilo_SilvermaneGuardRestrictedZone, floor="F1", position=(225.3, 425.9))
        enemy = Waypoint((170.4, 428.6))
        reward = Waypoint((166.7, 419.1))
        exit_ = Waypoint((159.6, 434.6))

        self.clear_elite(enemy)
        self.domain_reward(reward)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====
