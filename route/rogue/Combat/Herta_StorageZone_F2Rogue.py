from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Herta_StorageZone
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Herta_StorageZone_F2Rogue_X351Y165(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((351.4, 165.3)), | 274.2     | 274      |
        | item     | Waypoint((342.4, 155.5)), | 274.2     | 274      |
        | enemy    | Waypoint((302.2, 165.1)), | 261.9     | 264      |
        | exit_    | Waypoint((299.2, 164.0)), | 2.6       | 262      |
        | exit1    | Waypoint((293.3, 173.9)), | 282.0     | 274      |
        | exit2    | Waypoint((293.2, 155.6)), | 282.0     | 274      |
        """
        self.map_init(plane=Herta_StorageZone, floor="F2Rogue", position=(351.4, 165.3))
        self.register_domain_exit(
            Waypoint((299.2, 164.0)), end_rotation=262,
            left_door=Waypoint((293.3, 173.9)), right_door=Waypoint((293.2, 155.6)))
        item = Waypoint((342.4, 155.5))
        enemy = Waypoint((302.2, 165.1))
        # ===== End of generated waypoints =====

        self.clear_item(item)
        self.clear_enemy(enemy)

    def Herta_StorageZone_F2Rogue_X365Y167(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((364.8, 166.5)), | 274.2     | 274      |
        | item     | Waypoint((330.0, 174.1)), | 271.8     | 267      |
        | enemy    | Waypoint((300.0, 165.6)), | 284.9     | 94       |
        | exit_    | Waypoint((303.8, 164.2)), | 271.8     | 267      |
        | exit1    | Waypoint((293.3, 173.9)), | 282.0     | 274      |
        | exit2    | Waypoint((293.2, 155.6)), | 282.0     | 274      |
        """
        self.map_init(plane=Herta_StorageZone, floor="F2Rogue", position=(364.8, 166.5))
        self.register_domain_exit(
            Waypoint((303.8, 164.2)), end_rotation=267,
            left_door=Waypoint((293.3, 173.9)), right_door=Waypoint((293.2, 155.6)))
        item = Waypoint((330.0, 174.1))
        enemy = Waypoint((300.0, 165.6))
        # ===== End of generated waypoints =====

        self.clear_item(item)
        self.clear_enemy(enemy)
