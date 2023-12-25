from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Herta_StorageZone
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Herta_StorageZone_F2_X515Y219(self):
        """
        | Waypoint    | Position                  | Direction | Rotation |
        | ----------- | ------------------------- | --------- | -------- |
        | spawn       | Waypoint((515.5, 219.3)), | 354.1     | 348      |
        | node1       | Waypoint((525.4, 181.0)), | 2.7       | 357      |
        | event       | Waypoint((531.8, 180.0)), | 23.8      | 22       |
        | enemy1right | Waypoint((518.8, 168.6)), | 75.1      | 253      |
        | item1       | Waypoint((537.0, 165.2)), | 30.1      | 27       |
        | enemy1left  | Waypoint((475.9, 166.1)), | 282.7     | 276      |
        | item2       | Waypoint((442.0, 196.5)), | 216.5     | 214      |
        | node2       | Waypoint((448.4, 180.6)), | 246.5     | 241      |
        | node3       | Waypoint((402.2, 199.4)), | 282.9     | 276      |
        | enemy3      | Waypoint((370.7, 163.1)), | 215.8     | 304      |
        | item4       | Waypoint((343.0, 157.2)), | 293.1     | 290      |
        | enemy4      | Waypoint((301.8, 164.4)), | 278.3     | 276      |
        | exit_       | Waypoint((300.4, 164.5)), | 274.2     | 274      |
        | exit1       | Waypoint((292.0, 171.0)), | 261.7     | 260      |
        | exit2       | Waypoint((292.6, 158.5)), | 282.9     | 281      |
        """
        self.map_init(plane=Herta_StorageZone, floor="F2", position=(515.5, 219.3))
        self.register_domain_exit(
            Waypoint((300.4, 164.5)), end_rotation=274,
            left_door=Waypoint((292.0, 171.0)), right_door=Waypoint((292.6, 158.5)))
        node1 = Waypoint((525.4, 181.0))
        event = Waypoint((531.8, 180.0))
        enemy1right = Waypoint((518.8, 168.6))
        item1 = Waypoint((537.0, 165.2))
        enemy1left = Waypoint((475.9, 166.1))
        item2 = Waypoint((442.0, 196.5))
        node2 = Waypoint((448.4, 180.6))
        node3 = Waypoint((402.2, 199.4))
        enemy3 = Waypoint((370.7, 163.1))
        item4 = Waypoint((343.0, 157.2))
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
            item2,
        )
        # 3
        self.clear_enemy(
            node3.straight_run(),
            enemy3.straight_run(),
        )
        # 4
        self.clear_item(
            enemy3,
            item4,
        )
        self.clear_enemy(
            enemy4.straight_run(),
        )
