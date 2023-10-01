from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_BackwaterPass
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_BackwaterPass_F1_X351Y641(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((351.4, 641.3)), | 274.2     | 274      |
        | enemy    | Waypoint((304.3, 640.6)), | 274.2     | 274      |
        | reward   | Waypoint((293.8, 632.4)), | 290.2     | 288      |
        | exit     | Waypoint((286.4, 646.7)), | 244.9     | 258      |
        """
        self.map_init(plane=Jarilo_BackwaterPass, floor="F1", position=(351.4, 641.3))
        enemy = Waypoint((304.3, 640.6))
        reward = Waypoint((293.8, 632.4))
        exit_ = Waypoint((286.4, 646.7))

        self.clear_elite(enemy)
        self.domain_reward(reward)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====
