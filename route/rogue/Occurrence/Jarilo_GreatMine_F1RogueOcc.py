from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_GreatMine
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_GreatMine_F1RogueOcc_X109Y423(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((109.3, 422.9)), | 337.2     | 334      |
        | item     | Waypoint((93.3, 399.2)),  | 327.8     | 324      |
        | event    | Waypoint((96.2, 382.0)),  | 354.1     | 350      |
        | exit_    | Waypoint((85.9, 381.5)),  | 334.8     | 331      |
        | exit1    | Waypoint((74.8, 379.4)),  | 334.8     | 334      |
        | exit2    | Waypoint((90.9, 370.5)),  | 334.8     | 334      |
        """
        self.map_init(plane=Jarilo_GreatMine, floor="F1RogueOcc", position=(109.3, 422.9))
        self.register_domain_exit(
            Waypoint((85.9, 381.5)), end_rotation=331,
            left_door=Waypoint((74.8, 379.4)), right_door=Waypoint((90.9, 370.5)))
        item = Waypoint((93.3, 399.2))
        event = Waypoint((96.2, 382.0))

        self.clear_item(item)
        self.clear_event(event)
        # ===== End of generated waypoints =====
