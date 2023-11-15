from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_ArtisanshipCommission
from tasks.map.route.base import locked_position
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_ArtisanshipCommission_F1_X169Y491(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((167.8, 491.0)), | 96.7      | 91       |
        | event    | Waypoint((218.7, 491.1)), | 96.7      | 94       |
        | exit_    | Waypoint((216.9, 490.9)), | 190.0     | 89       |
        | exit1    | Waypoint((222.6, 484.8)), | 86.3      | 82       |
        | exit2    | Waypoint((222.6, 496.6)), | 119.8     | 117      |
        """
        self.map_init(plane=Luofu_ArtisanshipCommission, floor="F1", position=(167.8, 491.0))
        self.register_domain_exit(
            Waypoint((216.9, 490.9)), end_rotation=89,
            left_door=Waypoint((222.6, 484.8)), right_door=Waypoint((222.6, 496.6)))
        event = Waypoint((218.7, 491.1))

        self.clear_event(event)
        # ===== End of generated waypoints =====

    @locked_position
    def Luofu_ArtisanshipCommission_F1_X205Y145(self):
        """
        | Waypoint       | Position                  | Direction | Rotation |
        | -------------- | ------------------------- | --------- | -------- |
        | spawn          | Waypoint((205.5, 145.5)), | 190.1     | 184      |
        | item           | Waypoint((223.0, 163.1)), | 143.8     | 140      |
        | event_X204Y179 | Waypoint((204.4, 179.9)), | 282.8     | 181      |
        | exit_X204Y179  | Waypoint((204.4, 179.9)), | 282.8     | 181      |
        | exit1_X213Y189 | Waypoint((213.5, 189.5)), | 179.9     | 179      |
        | exit2_X197Y189 | Waypoint((197.5, 189.4)), | 192.7     | 184      |
        """
        self.map_init(plane=Luofu_ArtisanshipCommission, floor="F1", position=(205.5, 145.5))
        self.register_domain_exit(
            Waypoint((204.4, 179.9)), end_rotation=181,
            left_door=Waypoint((213.5, 189.5)), right_door=Waypoint((197.5, 189.4)))
        item = Waypoint((223.0, 163.1))
        event_X204Y179 = Waypoint((204.4, 179.9))

        self.clear_item(item)
        self.clear_event(event_X204Y179)
        # ===== End of generated waypoints =====

    def Luofu_ArtisanshipCommission_F1_X521Y63(self):
        """
        | Waypoint | Position                 | Direction | Rotation |
        | -------- | ------------------------ | --------- | -------- |
        | spawn    | Waypoint((521.8, 63.6)), | 96.7      | 91       |
        | item     | Waypoint((536.8, 51.1)), | 62.6      | 57       |
        | event    | Waypoint((572.0, 64.2)), | 96.7      | 91       |
        | exit_    | Waypoint((572.8, 65.3)), | 193.0     | 91       |
        | exit1    | Waypoint((585.0, 55.0)), | 195.4     | 96       |
        | exit2    | Waypoint((581.0, 73.2)), | 101.0     | 96       |
        """
        self.map_init(plane=Luofu_ArtisanshipCommission, floor="F1", position=(521.8, 63.6))
        self.register_domain_exit(
            Waypoint((572.8, 65.3)), end_rotation=91,
            left_door=Waypoint((585.0, 55.0)), right_door=Waypoint((581.0, 73.2)))
        item = Waypoint((536.8, 51.1))
        event = Waypoint((572.0, 64.2))

        self.clear_item(item)
        self.clear_event(event)
        # ===== End of generated waypoints =====
