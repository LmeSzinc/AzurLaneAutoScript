from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Herta_StorageZone
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Herta_StorageZone_F2_X351Y164(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((351.4, 164.9)), | 274.2     | 274      |
        | item     | Waypoint((342.8, 155.7)), | 274.2     | 274      |
        | enemy    | Waypoint((304.0, 165.4)), | 261.9     | 264      |
        | exit     | Waypoint((300.8, 163.8)), | 2.6       | 262      |
        """
        self.map_init(plane=Herta_StorageZone, floor="F2", position=(351.4, 164.9))
        self.register_domain_exit(Waypoint((300.8, 163.8)), end_rotation=262)
        item = Waypoint((342.8, 155.7))
        enemy = Waypoint((304.0, 165.4))
        # ===== End of generated waypoints =====

        self.clear_item(item)
        self.clear_enemy(enemy)

    def Herta_StorageZone_F2_X365Y167(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((365.1, 167.2)), | 274.2     | 274      |
        | item     | Waypoint((330.0, 175.6)), | 271.8     | 267      |
        | enemy    | Waypoint((300.2, 166.0)), | 284.9     | 94       |
        | exit     | Waypoint((304.0, 166.0)), | 271.8     | 267      |
        """
        self.map_init(plane=Herta_StorageZone, floor="F2", position=(365.1, 167.2))
        self.register_domain_exit(Waypoint((304.0, 166.0)), end_rotation=267)
        item = Waypoint((330.0, 175.6))
        enemy = Waypoint((300.2, 166.0))
        # ===== End of generated waypoints =====

        self.clear_item(item)
        self.clear_enemy(enemy)

    def Herta_StorageZone_F2_X515Y219(self):
        """
        | Waypoint       | Position                  | Direction | Rotation |
        | -------------- | ------------------------- | --------- | -------- |
        | spawn          | Waypoint((515.5, 219.3)), | 354.1     | 348      |
        | node1          | Waypoint((525.4, 181.0)), | 2.7       | 357      |
        | event          | Waypoint((531.8, 180.0)), | 23.8      | 22       |
        | enemy1right    | Waypoint((518.8, 168.6)), | 75.1      | 253      |
        | item1          | Waypoint((537.0, 165.2)), | 30.1      | 27       |
        | enemy1left     | Waypoint((477.9, 162.1)), | 282.7     | 276      |
        | item2_X444Y196 | Waypoint((444.0, 196.5)), | 216.5     | 214      |
        | node2          | Waypoint((448.4, 180.6)), | 246.5     | 241      |
        | node3          | Waypoint((402.2, 199.4)), | 282.9     | 276      |
        | enemy3         | Waypoint((370.7, 163.1)), | 215.8     | 304      |
        | enemy4         | Waypoint((301.8, 164.4)), | 278.3     | 276      |
        | exit           | Waypoint((300.4, 164.5)), | 274.2     | 274      |
        """
        self.map_init(plane=Herta_StorageZone, floor="F2", position=(515.5, 219.3))
        self.register_domain_exit(Waypoint((300.4, 164.5)), end_rotation=274)
        node1 = Waypoint((525.4, 181.0))
        event = Waypoint((531.8, 180.0))
        enemy1right = Waypoint((518.8, 168.6))
        item1 = Waypoint((537.0, 165.2))
        enemy1left = Waypoint((477.9, 162.1))
        item2_X444Y196 = Waypoint((444.0, 196.5))
        node2 = Waypoint((448.4, 180.6))
        node3 = Waypoint((402.2, 199.4))
        enemy3 = Waypoint((370.7, 163.1))
        enemy4 = Waypoint((301.8, 164.4))
        # ===== End of generated waypoints =====

        # 1
        self.clear_item(
            # Ignore event, go through node1
            event.straight_run(),
            item1,
        )
        self.clear_enemy(
            enemy1right.straight_run(),
            enemy1left.straight_run(),
        )
        # 2
        self.clear_item(
            # Go through enemy1left
            enemy1left,
            node2.straight_run(),
            item2_X444Y196,
        )
        # 3
        self.clear_enemy(
            node3.straight_run(),
            enemy3.straight_run(),
        )
        # 4
        self.clear_enemy(
            enemy3,
            enemy4.straight_run(),
        )
