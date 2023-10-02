from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Herta_StorageZone
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Herta_StorageZone_F1_X257Y85(self):
        """
        | Waypoint | Position                 | Direction | Rotation |
        | -------- | ------------------------ | --------- | -------- |
        | spawn    | Waypoint((257.3, 85.5)), | 308.0     | 304      |
        | item     | Waypoint((244.2, 66.3)), | 334.7     | 331      |
        | door     | Waypoint((215.4, 65.1)), | 303.8     | 301      |
        | enemy    | Waypoint((202.7, 57.9)), | 297.8     | 294      |
        | exit     | Waypoint((202.4, 58.1)), | 302.9     | 301      |
        """
        self.map_init(plane=Herta_StorageZone, floor="F1", position=(257.3, 85.5))
        self.register_domain_exit(Waypoint((202.4, 58.1)), end_rotation=301)
        item = Waypoint((244.2, 66.3))
        door = Waypoint((215.4, 65.1))
        enemy = Waypoint((202.7, 57.9))
        # ===== End of generated waypoints =====

        self.clear_item(item)
        self.clear_enemy(door, enemy)

    def Herta_StorageZone_F1_X692Y61(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((692.0, 62.0)),  | 263.8     | 260      |
        | item1    | Waypoint((676.1, 98.5)),  | 222.6     | 218      |
        | enemy1   | Waypoint((658.6, 86.9)),  | 339.2     | 336      |
        | enemy2   | Waypoint((649.3, 68.7)),  | 354.1     | 350      |
        | item2    | Waypoint((642.2, 66.1)),  | 290.2     | 285      |
        | door     | Waypoint((640.2, 82.2)),  | 260.3     | 258      |
        | node     | Waypoint((599.2, 91.0)),  | 256.7     | 255      |
        | enemy3   | Waypoint((598.3, 129.1)), | 181.3     | 174      |
        | exit     | Waypoint((598.3, 129.1)), | 181.3     | 174      |
        """
        self.map_init(plane=Herta_StorageZone, floor="F1", position=(692.0, 62.0))
        self.register_domain_exit(Waypoint((598.3, 129.1)), end_rotation=174)
        item1 = Waypoint((676.1, 98.5))
        enemy1 = Waypoint((658.6, 86.9))
        enemy2 = Waypoint((649.3, 68.7))
        item2 = Waypoint((642.2, 66.1))
        door = Waypoint((640.2, 82.2))
        node = Waypoint((599.2, 91.0))
        enemy3 = Waypoint((598.3, 129.1))
        # ===== End of generated waypoints =====

        # item1
        self.clear_item(
            item1.straight_run(),
        )
        # enemy12
        self.clear_enemy(
            enemy1.straight_run(),
            enemy2,
        )
        self.clear_item(item2)
        # 3
        self.clear_enemy(
            door,
            node.straight_run(),
            enemy3.straight_run(),
        )
