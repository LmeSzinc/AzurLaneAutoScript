from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_ScalegorgeWaterscape
from tasks.map.route.base import locked_position, locked_rotation
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    @locked_rotation(180)
    def Luofu_ScalegorgeWaterscape_F1_X499Y135(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((499.5, 135.3)), | 190.1     | 184      |
        | event    | Waypoint((500.8, 169.1)), | 193.0     | 186      |
        | exit_    | Waypoint((499.2, 169.4)), | 187.1     | 179      |
        | exit1    | Waypoint((504.2, 176.2)), | 198.6     | 193      |
        | exit2    | Waypoint((495.3, 175.8)), | 198.6     | 193      |
        """
        self.map_init(plane=Luofu_ScalegorgeWaterscape, floor="F1", position=(499.5, 135.3))
        self.register_domain_exit(
            Waypoint((499.2, 169.4)), end_rotation=179,
            left_door=Waypoint((504.2, 176.2)), right_door=Waypoint((495.3, 175.8)))
        event = Waypoint((500.8, 169.1))

        self.clear_event(event)
        # ===== End of generated waypoints =====

    @locked_rotation(180)
    def Luofu_ScalegorgeWaterscape_F1_X619Y387(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((619.4, 387.3)), | 190.1     | 184      |
        | item     | Waypoint((626.2, 408.2)), | 157.2     | 151      |
        | event    | Waypoint((622.3, 422.5)), | 190.1     | 186      |
        | exit_    | Waypoint((619.0, 423.6)), | 190.1     | 184      |
        | exit1    | Waypoint((623.4, 427.5)), | 192.6     | 181      |
        | exit2    | Waypoint((613.5, 427.5)), | 192.6     | 184      |
        """
        self.map_init(plane=Luofu_ScalegorgeWaterscape, floor="F1", position=(619.4, 387.3))
        self.register_domain_exit(
            Waypoint((619.0, 423.6)), end_rotation=184,
            left_door=Waypoint((623.4, 427.5)), right_door=Waypoint((613.5, 427.5)))
        item = Waypoint((626.2, 408.2))
        event = Waypoint((622.3, 422.5))

        self.clear_item(item)
        self.clear_event(event)
        # ===== End of generated waypoints =====

    @locked_position
    def Luofu_ScalegorgeWaterscape_F1_X714Y243(self):
        """
        | Waypoint      | Position                  | Direction | Rotation |
        | ------------- | ------------------------- | --------- | -------- |
        | spawn         | Waypoint((714.4, 243.2)), | 274.2     | 274      |
        | item_X694Y254 | Waypoint((694.2, 254.8)), | 256.7     | 258      |
        | event         | Waypoint((678.9, 243.0)), | 274.2     | 274      |
        | exit_         | Waypoint((677.4, 243.2)), | 274.2     | 271      |
        | exit1         | Waypoint((672.6, 246.7)), | 272.7     | 267      |
        | exit2         | Waypoint((673.6, 238.2)), | 272.8     | 269      |
        """
        self.map_init(plane=Luofu_ScalegorgeWaterscape, floor="F1", position=(714.4, 243.2))
        self.register_domain_exit(
            Waypoint((677.4, 243.2)), end_rotation=271,
            left_door=Waypoint((672.6, 246.7)), right_door=Waypoint((673.6, 238.2)))
        item_X694Y254 = Waypoint((694.2, 254.8))
        event = Waypoint((678.9, 243.0))

        self.clear_item(item_X694Y254)
        self.clear_event(event)
        # ===== End of generated waypoints =====
