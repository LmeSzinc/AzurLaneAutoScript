from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_StargazerNavalia
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_StargazerNavalia_F1_X250Y498(self):
        """
        | Waypoint       | Position                  | Direction | Rotation |
        | -------------- | ------------------------- | --------- | -------- |
        | spawn          | Waypoint((249.4, 498.5)), | 190.1     | 184      |
        | event_X236Y528 | Waypoint((236.8, 528.9)), | 188.1     | 181      |
        | exit           | Waypoint((245.3, 550.1)), | 282.9     | 181      |
        """
        self.map_init(plane=Luofu_StargazerNavalia, floor="F1", position=(249.4, 498.5))
        self.register_domain_exit(Waypoint((245.3, 550.1)), end_rotation=181)
        event_X236Y528 = Waypoint((236.8, 528.9))

        self.clear_event(event_X236Y528)
        # ===== End of generated waypoints =====

    def Luofu_StargazerNavalia_F1_X521Y595(self):
        """
        | Waypoint       | Position                  | Direction | Rotation |
        | -------------- | ------------------------- | --------- | -------- |
        | spawn          | Waypoint((521.6, 595.4)), | 190.1     | 184      |
        | event_X510Y626 | Waypoint((510.6, 626.4)), | 282.9     | 181      |
        | exit           | Waypoint((522.2, 630.6)), | 190.0     | 184      |
        """
        self.map_init(plane=Luofu_StargazerNavalia, floor="F1", position=(521.6, 595.4))
        self.register_domain_exit(Waypoint((522.2, 630.6)), end_rotation=184)
        event_X510Y626 = Waypoint((510.6, 626.4))

        self.clear_event(event_X510Y626)
        # ===== End of generated waypoints =====
