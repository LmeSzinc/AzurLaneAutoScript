from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_CorridorofFadingEchoes
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_CorridorofFadingEchoes_F1_X115Y911(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((115.5, 911.3)), | 274.2     | 274      |
        | enemy    | Waypoint((64.2, 909.2)),  | 282.6     | 276      |
        | exit     | Waypoint((64.2, 909.2)),  | 282.6     | 276      |
        """
        self.map_init(plane=Jarilo_CorridorofFadingEchoes, floor="F1", position=(115.5, 911.3))
        self.register_domain_exit(Waypoint((64.2, 909.2)), end_rotation=276)
        enemy = Waypoint((64.2, 909.2))
        # ===== End of generated waypoints =====

        self.clear_enemy(enemy)

    def Jarilo_CorridorofFadingEchoes_F1_X201Y1071(self):
        """
        | Waypoint    | Position                   | Direction | Rotation |
        | ----------- | -------------------------- | --------- | -------- |
        | spawn       | Waypoint((201.2, 1071.4)), | 6.7       | 4        |
        | enemy1right | Waypoint((200.3, 1032.4)), | 342.0     | 343      |
        | enemy1left  | Waypoint((168.6, 1022.3)), | 279.8     | 89       |
        | node2       | Waypoint((118.4, 1019.0)), | 282.9     | 285      |
        | enemy2left  | Waypoint((105.2, 1012.0)), | 317.9     | 315      |
        | enemy2right | Waypoint((102.2, 976.4)),  | 11.1      | 193      |
        | enemy3      | Waypoint((103.4, 919.2)),  | 6.7       | 4        |
        | exit        | Waypoint((103.4, 919.2)),  | 6.7       | 4        |
        """
        self.map_init(plane=Jarilo_CorridorofFadingEchoes, floor="F1", position=(201.2, 1071.4))
        self.register_domain_exit(Waypoint((103.4, 919.2)), end_rotation=4)
        enemy1right = Waypoint((200.3, 1032.4))
        enemy1left = Waypoint((168.6, 1022.3))
        node2 = Waypoint((118.4, 1019.0))
        enemy2left = Waypoint((105.2, 1012.0))
        enemy2right = Waypoint((102.2, 976.4))
        enemy3 = Waypoint((103.4, 919.2))
        # ===== End of generated waypoints =====

        # 1
        self.rotation_set(315)
        self.clear_enemy(
            enemy1right.set_threshold(5),
            enemy1left.set_threshold(5),
        )
        # 2
        self.clear_enemy(
            enemy1left.set_threshold(3),
            node2.set_threshold(5),
            enemy2left.straight_run(),
            enemy2right,
        )
        # 3
        self.clear_enemy(enemy3)

    def Jarilo_CorridorofFadingEchoes_F1_X266Y457(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((267.0, 457.2)), | 274.2     | 274      |
        | enemy    | Waypoint((220.2, 457.6)), | 185.8     | 274      |
        | exit     | Waypoint((208.6, 458.6)), | 274.2     | 276      |
        """
        self.map_init(plane=Jarilo_CorridorofFadingEchoes, floor="F1", position=(267.0, 457.2))
        self.register_domain_exit(Waypoint((208.6, 458.6)), end_rotation=276)
        enemy = Waypoint((220.2, 457.6))
        # ===== End of generated waypoints =====

        self.clear_enemy(enemy)

    def Jarilo_CorridorofFadingEchoes_F1_X291Y765(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((291.1, 765.3)), | 190.1     | 184      |
        | item     | Waypoint((282.1, 782.4)), | 216.3     | 211      |
        | enemy    | Waypoint((291.2, 821.2)), | 188.1     | 181      |
        | exit     | Waypoint((291.2, 821.2)), | 188.1     | 181      |
        """
        self.map_init(plane=Jarilo_CorridorofFadingEchoes, floor="F1", position=(291.1, 765.3))
        self.register_domain_exit(Waypoint((291.2, 821.2)), end_rotation=181)
        item = Waypoint((282.1, 782.4))
        enemy = Waypoint((291.2, 821.2))
        # ===== End of generated waypoints =====

        self.clear_item(item)
        self.clear_enemy(enemy)

    def Jarilo_CorridorofFadingEchoes_F1_X319Y949(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((319.4, 949.3)), | 96.7      | 91       |
        | item     | Waypoint((340.4, 940.6)), | 59.1      | 54       |
        | enemy    | Waypoint((380.2, 948.0)), | 261.8     | 73       |
        | exit     | Waypoint((386.2, 944.2)), | 96.7      | 89       |
        """
        self.map_init(plane=Jarilo_CorridorofFadingEchoes, floor="F1", position=(319.4, 949.3))
        self.register_domain_exit(Waypoint((386.2, 944.2)), end_rotation=89)
        item = Waypoint((340.4, 940.6))
        enemy = Waypoint((380.2, 948.0))
        # ===== End of generated waypoints =====

        # Ignore item, bad way
        self.clear_enemy(enemy)

    def Jarilo_CorridorofFadingEchoes_F1_X369Y439(self):
        """
        | Waypoint    | Position                  | Direction | Rotation |
        | ----------- | ------------------------- | --------- | -------- |
        | spawn       | Waypoint((369.4, 439.2)), | 96.7      | 91       |
        | enemy1      | Waypoint((408.2, 430.6)), | 87.7      | 80       |
        | enemy2right | Waypoint((444.6, 466.0)), | 129.8     | 124      |
        | enemy4      | Waypoint((452.2, 392.2)), | 318.0     | 318      |
        | enemy2left  | Waypoint((475.0, 462.4)), | 67.2      | 64       |
        | node4       | Waypoint((493.0, 437.4)), | 4.1       | 359      |
        | node3       | Waypoint((493.0, 449.0)), | 190.0     | 43       |
        | exit        | Waypoint((452.2, 392.2)), | 318.0     | 318      |
        """
        self.map_init(plane=Jarilo_CorridorofFadingEchoes, floor="F1", position=(369.4, 439.2))
        self.register_domain_exit(Waypoint((452.2, 392.2)), end_rotation=318)
        enemy1 = Waypoint((408.2, 430.6))
        enemy2right = Waypoint((444.6, 466.0))
        enemy4 = Waypoint((452.2, 392.2))
        enemy2left = Waypoint((475.0, 462.4))
        node4 = Waypoint((493.0, 437.4))
        node3 = Waypoint((493.0, 449.0))
        # ===== End of generated waypoints =====

        self.clear_enemy(enemy1)
        self.clear_enemy(
            enemy2right.straight_run(),
            enemy2left.straight_run(),
        )
        self.clear_enemy(
            node3.straight_run(),
            node4.straight_run(),
            enemy4.straight_run(),
        )

    def Jarilo_CorridorofFadingEchoes_F1_X463Y123(self):
        """
        | Waypoint      | Position                  | Direction | Rotation |
        | ------------- | ------------------------- | --------- | -------- |
        | spawn         | Waypoint((463.3, 123.5)), | 96.7      | 91       |
        | item_X476Y129 | Waypoint((476.9, 129.9)), | 116.8     | 114      |
        | enemy1        | Waypoint((544.4, 128.5)), | 129.9     | 128      |
        | node2         | Waypoint((554.6, 143.6)), | 166.6     | 158      |
        | enemy2        | Waypoint((556.4, 206.8)), | 190.1     | 184      |
        | exit          | Waypoint((556.4, 206.8)), | 190.1     | 184      |
        """
        self.map_init(plane=Jarilo_CorridorofFadingEchoes, floor="F1", position=(463.3, 123.5))
        self.register_domain_exit(Waypoint((556.4, 206.8)), end_rotation=184)
        item_X476Y129 = Waypoint((476.9, 129.9))
        enemy1 = Waypoint((544.4, 128.5))
        node2 = Waypoint((554.6, 143.6))
        enemy2 = Waypoint((556.4, 206.8))
        # ===== End of generated waypoints =====

        self.rotation_set(158)
        self.clear_item(item_X476Y129)
        self.clear_enemy(enemy1)
        self.clear_enemy(enemy2.straight_run())
