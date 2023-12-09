from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Herta_StorageZone
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Herta_StorageZone_F2Rogue_X363Y166(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((363.4, 165.6)), | 274.2     | 274      |
        | item     | Waypoint((331.9, 173.0)), | 263.8     | 260      |
        | event    | Waypoint((318.6, 156.8)), | 290.1     | 285      |
        | exit_    | Waypoint((314.1, 164.2)), | 276.0     | 271      |
        | exit1    | Waypoint((303.2, 171.0)), | 275.9     | 274      |
        | exit2    | Waypoint((303.2, 160.4)), | 277.8     | 276      |
        """
        self.map_init(plane=Herta_StorageZone, floor="F2Rogue", position=(363.4, 165.6))
        self.register_domain_exit(
            Waypoint((314.1, 164.2)), end_rotation=271,
            left_door=Waypoint((303.2, 171.0)), right_door=Waypoint((303.2, 160.4)))
        item = Waypoint((331.9, 173.0))
        event = Waypoint((318.6, 156.8))

        self.clear_item(item)
        self.clear_event(event)
        # ===== End of generated waypoints =====
