from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_GreatMine
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_GreatMine_F1_X175Y273(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((175.5, 273.5)), | 274.2     | 274      |
        | enemy    | Waypoint((128.5, 273.0)), | 282.9     | 271      |
        | reward   | Waypoint((116.8, 265.0)), | 293.1     | 290      |
        | exit     | Waypoint((111.5, 280.3)), | 250.7     | 248      |
        """
        self.map_init(plane=Jarilo_GreatMine, floor="F1", position=(175.5, 273.5))
        enemy = Waypoint((128.5, 273.0))
        reward = Waypoint((116.8, 265.0))
        exit_ = Waypoint((111.5, 280.3))

        self.clear_elite(enemy)
        self.domain_reward(reward)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====

    def Jarilo_GreatMine_F1_X303Y489(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((303.4, 489.3)), | 6.7       | 4        |
        | enemy    | Waypoint((304.2, 441.8)), | 6.7       | 4        |
        | reward   | Waypoint((310.9, 430.8)), | 30.1      | 27       |
        | exit     | Waypoint((296.5, 421.4)), | 342.1     | 343      |
        """
        self.map_init(plane=Jarilo_GreatMine, floor="F1", position=(303.4, 489.3))
        enemy = Waypoint((304.2, 441.8))
        reward = Waypoint((310.9, 430.8))
        exit_ = Waypoint((296.5, 421.4))

        self.clear_elite(enemy)
        self.domain_reward(reward)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====
