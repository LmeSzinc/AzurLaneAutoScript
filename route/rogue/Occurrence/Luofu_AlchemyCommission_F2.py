from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_AlchemyCommission
from tasks.map.route.base import locked_rotation
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_AlchemyCommission_F2_X473Y867(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((473.7, 867.7)), | 282.2     | 274      |
        | event    | Waypoint((421.4, 868.6)), | 282.0     | 274      |
        | exit_    | Waypoint((419.3, 867.5)), | 277.8     | 274      |
        | exit1    | Waypoint((407.9, 880.7)), | 282.0     | 274      |
        | exit2    | Waypoint((410.9, 858.4)), | 281.8     | 274      |
        """
        self.map_init(plane=Luofu_AlchemyCommission, floor="F2", position=(473.7, 867.7))
        self.register_domain_exit(
            Waypoint((419.3, 867.5)), end_rotation=274,
            left_door=Waypoint((407.9, 880.7)), right_door=Waypoint((410.9, 858.4)))
        event = Waypoint((421.4, 868.6))

        self.clear_event(event)
        # ===== End of generated waypoints =====

    @locked_rotation(270)
    def Luofu_AlchemyCommission_F2_X487Y589(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((487.4, 589.4)), | 282.2     | 274      |
        | event    | Waypoint((434.8, 590.6)), | 282.8     | 276      |
        | exit_    | Waypoint((434.2, 590.0)), | 274.2     | 271      |
        | exit1    | Waypoint((425.4, 598.6)), | 272.7     | 267      |
        | exit2    | Waypoint((427.2, 581.1)), | 272.7     | 269      |
        """
        self.map_init(plane=Luofu_AlchemyCommission, floor="F2", position=(487.4, 589.4))
        self.register_domain_exit(
            Waypoint((434.2, 590.0)), end_rotation=271,
            left_door=Waypoint((425.4, 598.6)), right_door=Waypoint((427.2, 581.1)))
        event = Waypoint((434.8, 590.6))

        self.clear_event(event)
        # ===== End of generated waypoints =====

    def Luofu_AlchemyCommission_F2_X517Y374(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((517.5, 374.1)), | 146.7     | 140      |
        | event    | Waypoint((554.5, 411.0)), | 135.9     | 140      |
        | exit_    | Waypoint((554.6, 410.8)), | 48.1      | 140      |
        | exit1    | Waypoint((568.4, 412.6)), | 148.1     | 140      |
        | exit2    | Waypoint((555.0, 423.4)), | 135.9     | 140      |
        """
        self.map_init(plane=Luofu_AlchemyCommission, floor="F2", position=(517.5, 374.1))
        self.register_domain_exit(
            Waypoint((554.6, 410.8)), end_rotation=140,
            left_door=Waypoint((568.4, 412.6)), right_door=Waypoint((555.0, 423.4)))
        event = Waypoint((554.5, 411.0))

        self.clear_event(event)
        # ===== End of generated waypoints =====
