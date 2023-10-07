from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Herta_SupplyZone
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Herta_SupplyZone_F2_X641Y247(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((657.1, 247.5)), | 96.7      | 91       |
        | enemy    | Waypoint((726.4, 246.6)), | 99.0      | 94       |
        | reward   | Waypoint((738.2, 254.2)), | 166.6     | 112      |
        | exit     | Waypoint((746.0, 240.0)), | 82.8      | 75       |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2", position=(641, 247.5))
        enemy = Waypoint((726.4, 246.6))
        reward = Waypoint((738.2, 254.2))
        exit_ = Waypoint((746.0, 240.0))

        self.clear_elite(enemy)
        self.domain_reward(reward)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====

        """
        Notes
        Herta_SupplyZone_F2_X641Y247 is the same as Herta_SupplyZone_F2_X657Y247
        but for wrong spawn point detected
        """

    def Herta_SupplyZone_F2_X657Y247(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((657.1, 247.5)), | 96.7      | 91       |
        | enemy    | Waypoint((726.4, 246.6)), | 99.0      | 94       |
        | reward   | Waypoint((738.2, 254.2)), | 166.6     | 112      |
        | exit     | Waypoint((746.0, 240.0)), | 82.8      | 75       |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2", position=(657.1, 247.5))
        enemy = Waypoint((726.4, 246.6))
        reward = Waypoint((738.2, 254.2))
        exit_ = Waypoint((746.0, 240.0))

        self.clear_elite(enemy)
        self.domain_reward(reward)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====
