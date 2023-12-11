from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_StargazerNavalia
from tasks.map.route.base import locked_rotation
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    @locked_rotation(180)
    def Luofu_StargazerNavalia_F1Rogue_X250Y498(self):
        """
        | Waypoint       | Position                  | Direction | Rotation |
        | -------------- | ------------------------- | --------- | -------- |
        | spawn          | Waypoint((249.4, 498.5)), | 190.1     | 184      |
        | event          | Waypoint((236.9, 535.2)), | 206.2     | 200      |
        | exit_          | Waypoint((245.3, 550.1)), | 282.9     | 181      |
        | exit1_X255Y562 | Waypoint((255.5, 562.5)), | 180.1     | 184      |
        | exit2_X237Y559 | Waypoint((237.4, 559.3)), | 191.8     | 184      |
        """
        self.map_init(plane=Luofu_StargazerNavalia, floor="F1Rogue", position=(249.4, 498.5))
        self.register_domain_exit(
            Waypoint((245.3, 550.1)), end_rotation=181,
            left_door=Waypoint((255.5, 562.5)), right_door=Waypoint((237.4, 559.3)))
        event = Waypoint((236.9, 535.2))

        self.clear_event(event)
        # ===== End of generated waypoints =====
