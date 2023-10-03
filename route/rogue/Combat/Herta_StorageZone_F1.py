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

    def Herta_StorageZone_F1_X273Y92(self):
        """
        | Waypoint      | Position                 | Direction | Rotation |
        | ------------- | ------------------------ | --------- | -------- |
        | spawn         | Waypoint((273.4, 92.2)), | 308.0     | 304      |
        | item          | Waypoint((248.4, 59.4)), | 334.8     | 331      |
        | enemy_X227Y69 | Waypoint((227.8, 69.5)), | 30.2      | 299      |
        | exit_X227Y69  | Waypoint((227.8, 69.5)), | 30.2      | 299      |
        """
        self.map_init(plane=Herta_StorageZone, floor="F1", position=(273.4, 92.2))
        self.register_domain_exit(Waypoint((227.8, 69.5)), end_rotation=299)
        item = Waypoint((248.4, 59.4))
        enemy_X227Y69 = Waypoint((227.8, 69.5))
        # ===== End of generated waypoints =====

        # Ignore item, bad way
        self.clear_enemy(enemy_X227Y69)

    def Herta_StorageZone_F1_X692Y61(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((692.0, 62.0)),  | 263.8     | 260      |
        | item1    | Waypoint((676.1, 98.5)),  | 222.6     | 218      |
        | enemy2   | Waypoint((649.3, 68.7)),  | 354.1     | 350      |
        | enemy1   | Waypoint((654.7, 84.5)),  | 282.9     | 288      |
        | item2    | Waypoint((642.2, 66.1)),  | 290.2     | 285      |
        | door     | Waypoint((640.2, 82.2)),  | 260.3     | 258      |
        | node     | Waypoint((599.2, 91.0)),  | 256.7     | 255      |
        | enemy3   | Waypoint((598.3, 129.1)), | 181.3     | 174      |
        | exit     | Waypoint((598.3, 129.1)), | 181.3     | 174      |
        """
        self.map_init(plane=Herta_StorageZone, floor="F1", position=(692.0, 62.0))
        self.register_domain_exit(Waypoint((598.3, 129.1)), end_rotation=174)
        item1 = Waypoint((676.1, 98.5))
        enemy2 = Waypoint((649.3, 68.7))
        enemy1 = Waypoint((654.7, 84.5))
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
            door.set_threshold(3),
            node.straight_run(),
            enemy3.straight_run(),
        )

    def Herta_StorageZone_F1_X769Y39(self):
        """
        | Waypoint    | Position                  | Direction | Rotation |
        | ----------- | ------------------------- | --------- | -------- |
        | spawn       | Waypoint((749.5, 45.6)),  | 263.8     | 260      |
        | item1       | Waypoint((728.9, 48.8)),  | 263.8     | 264      |
        | enemy1      | Waypoint((686.2, 64.4)),  | 256.8     | 260      |
        | item2       | Waypoint((674.0, 99.1)),  | 212.9     | 204      |
        | enemy2left  | Waypoint((653.4, 85.0)),  | 326.7     | 103      |
        | node2       | Waypoint((636.8, 81.9)),  | 263.8     | 262      |
        | enemy2right | Waypoint((628.0, 73.6)),  | 350.2     | 345      |
        | node3       | Waypoint((598.6, 93.9)),  | 256.7     | 253      |
        | item3       | Waypoint((588.6, 102.2)), | 245.0     | 246      |
        | enemy3      | Waypoint((597.2, 131.0)), | 282.9     | 179      |
        | exit        | Waypoint((597.2, 131.0)), | 282.9     | 179      |
        """
        self.map_init(plane=Herta_StorageZone, floor="F1", position=(749.5, 45.6))
        self.register_domain_exit(Waypoint((597.2, 131.0)), end_rotation=179)
        item1 = Waypoint((728.9, 48.8))
        enemy1 = Waypoint((686.2, 64.4))
        item2 = Waypoint((674.0, 99.1))
        enemy2left = Waypoint((653.4, 85.0))
        node2 = Waypoint((636.8, 81.9))
        enemy2right = Waypoint((628.0, 73.6))
        node3 = Waypoint((598.6, 93.9))
        item3 = Waypoint((588.6, 102.2))
        enemy3 = Waypoint((597.2, 131.0))
        # ===== End of generated waypoints =====

        # 1
        self.clear_item(item1)
        self.clear_enemy(enemy1)
        # 2
        self.clear_item(item2.straight_run())
        self.clear_enemy(
            enemy2left.straight_run(),
            enemy2right.straight_run(),
        )
        # 3
        self.clear_item(
            node2.set_threshold(3),
            node3.straight_run(),
            item3,
        )
        self.clear_enemy(enemy3.straight_run())
