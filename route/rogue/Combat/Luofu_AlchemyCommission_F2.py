from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_AlchemyCommission
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_AlchemyCommission_F2_X415Y589(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((415.5, 589.4)), | 94.2      | 91       |
        | enemy    | Waypoint((469.2, 591.0)), | 189.1     | 89       |
        | exit_    | Waypoint((469.2, 591.0)), | 189.1     | 89       |
        | exit1    | Waypoint((478.2, 580.4)), | 97.0      | 89       |
        | exit2    | Waypoint((478.1, 598.6)), | 97.9      | 89       |
        """
        self.map_init(plane=Luofu_AlchemyCommission, floor="F2", position=(415.5, 589.4))
        self.register_domain_exit(
            Waypoint((469.2, 591.0)), end_rotation=89,
            left_door=Waypoint((478.2, 580.4)), right_door=Waypoint((478.1, 598.6)))
        enemy = Waypoint((469.2, 591.0))
        # ===== End of generated waypoints =====

        self.clear_enemy(enemy)

    def Luofu_AlchemyCommission_F2_X447Y508(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((447.4, 508.1)), | 59.1      | 48       |
        | enemy    | Waypoint((494.8, 461.2)), | 149.0     | 48       |
        | exit_    | Waypoint((494.8, 461.2)), | 149.0     | 48       |
        | exit1    | Waypoint((494.0, 448.0)), | 59.1      | 48       |
        | exit2    | Waypoint((506.8, 460.8)), | 59.1      | 48       |
        """
        self.map_init(plane=Luofu_AlchemyCommission, floor="F2", position=(447.4, 508.1))
        self.register_domain_exit(
            Waypoint((494.8, 461.2)), end_rotation=48,
            left_door=Waypoint((494.0, 448.0)), right_door=Waypoint((506.8, 460.8)))
        enemy = Waypoint((494.8, 461.2))
        # ===== End of generated waypoints =====

        self.clear_enemy(enemy)

    def Luofu_AlchemyCommission_F2_X454Y501(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((447.4, 508.1)), | 59.1      | 48       |
        | enemy    | Waypoint((494.8, 461.2)), | 149.0     | 48       |
        | exit_    | Waypoint((494.8, 461.2)), | 149.0     | 48       |
        | exit1    | Waypoint((494.0, 448.0)), | 59.1      | 48       |
        | exit2    | Waypoint((506.8, 460.8)), | 59.1      | 48       |
        """
        self.map_init(plane=Luofu_AlchemyCommission, floor="F2", position=(453.7, 501.3))
        self.register_domain_exit(
            Waypoint((494.8, 461.2)), end_rotation=48,
            left_door=Waypoint((494.0, 448.0)), right_door=Waypoint((506.8, 460.8)))
        enemy = Waypoint((494.8, 461.2))
        # ===== End of generated waypoints =====

        self.clear_enemy(enemy)

        # Same as Luofu_AlchemyCommission_F2_X447Y508

    def Luofu_AlchemyCommission_F2_X457Y497(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((447.4, 508.1)), | 59.1      | 48       |
        | enemy    | Waypoint((494.8, 461.2)), | 149.0     | 48       |
        | exit_    | Waypoint((494.8, 461.2)), | 149.0     | 48       |
        | exit1    | Waypoint((494.0, 448.0)), | 59.1      | 48       |
        | exit2    | Waypoint((506.8, 460.8)), | 59.1      | 48       |
        """
        self.map_init(plane=Luofu_AlchemyCommission, floor="F2", position=(457, 497))
        self.register_domain_exit(
            Waypoint((494.8, 461.2)), end_rotation=48,
            left_door=Waypoint((494.0, 448.0)), right_door=Waypoint((506.8, 460.8)))
        enemy = Waypoint((494.8, 461.2))
        # ===== End of generated waypoints =====

        self.clear_enemy(enemy)

        # Same as Luofu_AlchemyCommission_F2_X447Y508
