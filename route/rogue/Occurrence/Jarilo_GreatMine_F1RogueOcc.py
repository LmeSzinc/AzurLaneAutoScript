from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_GreatMine
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_GreatMine_F1RogueOcc_X109Y423(self):
        """
        | Waypoint      | Position                  | Direction | Rotation |
        | ------------- | ------------------------- | --------- | -------- |
        | spawn         | Waypoint((119.3, 444.9)), | 337.2     | 334      |
        | event_X96Y382 | Waypoint((96.2, 382.0)),  | 354.1     | 350      |
        | exit_X85Y381  | Waypoint((85.9, 381.5)),  | 334.8     | 331      |
        """
        self.map_init(plane=Jarilo_GreatMine, floor="F1RogueOcc", position=(109, 423))
        self.register_domain_exit(Waypoint((85.9, 381.5)), end_rotation=331)
        event_X96Y382 = Waypoint((96.2, 382.0))

        self.clear_event(event_X96Y382)
        # ===== End of generated waypoints =====

        """
        Notes
        Jarilo_GreatMine_F1RogueOcc_X109Y423 is the same as Jarilo_GreatMine_F1RogueOcc_X119Y444
        but for wrong spawn point detected
        """

    def Jarilo_GreatMine_F1RogueOcc_X119Y444(self):
        """
        | Waypoint      | Position                  | Direction | Rotation |
        | ------------- | ------------------------- | --------- | -------- |
        | spawn         | Waypoint((119.3, 444.9)), | 337.2     | 334      |
        | event_X96Y382 | Waypoint((96.2, 382.0)),  | 354.1     | 350      |
        | exit_X85Y381  | Waypoint((85.9, 381.5)),  | 334.8     | 331      |
        """
        self.map_init(plane=Jarilo_GreatMine, floor="F1RogueOcc", position=(119.3, 444.9))
        self.register_domain_exit(Waypoint((85.9, 381.5)), end_rotation=331)
        event_X96Y382 = Waypoint((96.2, 382.0))

        self.clear_event(event_X96Y382)
        # ===== End of generated waypoints =====
