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
