from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_DivinationCommission
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_DivinationCommission_F2_X149Y659(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((149.3, 659.3)), | 94.2      | 91       |
        | event    | Waypoint((201.1, 659.2)), | 94.2      | 91       |
        | exit_    | Waypoint((201.2, 661.0)), | 190.0     | 87       |
        | exit1    | Waypoint((211.2, 651.0)), | 96.8      | 87       |
        | exit2    | Waypoint((210.9, 669.0)), | 96.8      | 87       |
        """
        self.map_init(plane=Luofu_DivinationCommission, floor="F2", position=(149.3, 659.3))
        self.register_domain_exit(
            Waypoint((201.2, 661.0)), end_rotation=87,
            left_door=Waypoint((211.2, 651.0)), right_door=Waypoint((210.9, 669.0)))
        event = Waypoint((201.1, 659.2))

        self.clear_event(event)
        # ===== End of generated waypoints =====

    def Luofu_DivinationCommission_F2_X337Y799(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((337.4, 799.4)), | 4.5       | 4        |
        | event    | Waypoint((337.3, 745.2)), | 4.4       | 359      |
        | exit_    | Waypoint((337.1, 742.5)), | 4.4       | 4        |
        | exit1    | Waypoint((328.6, 736.8)), | 12.7      | 359      |
        | exit2    | Waypoint((345.0, 736.2)), | 12.7      | 6        |
        """
        self.map_init(plane=Luofu_DivinationCommission, floor="F2", position=(337.4, 799.4))
        self.register_domain_exit(
            Waypoint((337.1, 742.5)), end_rotation=4,
            left_door=Waypoint((328.6, 736.8)), right_door=Waypoint((345.0, 736.2)))
        event = Waypoint((337.3, 745.2))

        self.clear_event(event)
        # ===== End of generated waypoints =====

    def Luofu_DivinationCommission_F2_X425Y791(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((425.6, 791.4)), | 94.2      | 91       |
        | event    | Waypoint((478.9, 791.0)), | 96.8      | 94       |
        | exit_    | Waypoint((477.2, 789.2)), | 4.3       | 94       |
        | exit1    | Waypoint((487.2, 781.5)), | 96.8      | 89       |
        | exit2    | Waypoint((487.2, 799.2)), | 96.8      | 89       |
        """
        self.map_init(plane=Luofu_DivinationCommission, floor="F2", position=(425.6, 791.4))
        self.register_domain_exit(
            Waypoint((477.2, 789.2)), end_rotation=94,
            left_door=Waypoint((487.2, 781.5)), right_door=Waypoint((487.2, 799.2)))
        event = Waypoint((478.9, 791.0))

        self.clear_event(event)
        # ===== End of generated waypoints =====
