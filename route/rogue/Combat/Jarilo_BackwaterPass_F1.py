from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_BackwaterPass
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_BackwaterPass_F1_X475Y49(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((475.2, 49.5)),  | 190.1     | 184      |
        | item1    | Waypoint((468.4, 77.7)),  | 203.1     | 200      |
        | enemy1   | Waypoint((475.6, 99.4)),  | 30.1      | 184      |
        | item2    | Waypoint((448.4, 116.3)), | 245.9     | 248      |
        | enemy2   | Waypoint((464.2, 168.0)), | 166.8     | 341      |
        | enemy3   | Waypoint((500.9, 202.8)), | 135.8     | 133      |
        | exit     | Waypoint((500.9, 202.8)), | 135.8     | 133      |
        """
        self.map_init(plane=Jarilo_BackwaterPass, floor="F1", position=(475.2, 49.5))
        self.register_domain_exit(Waypoint((500.9, 202.8)), end_rotation=133)
        item1 = Waypoint((468.4, 77.7))
        enemy1 = Waypoint((475.6, 99.4))
        item2 = Waypoint((448.4, 116.3))
        enemy2 = Waypoint((464.2, 168.0))
        enemy3 = Waypoint((500.9, 202.8))
        # ===== End of generated waypoints =====

        # 1
        self.clear_item(item1)
        self.clear_enemy(enemy1)
        # 2
        self.clear_item(
            item2.straight_run(),
        )
        self.clear_enemy(
            enemy2.straight_run(),
        )
        # 3
        self.clear_enemy(
            enemy3.straight_run(),
        )

    def Jarilo_BackwaterPass_F1_X483Y105(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((483.5, 105.1)), | 275.8     | 87       |
        | enemy    | Waypoint((457.4, 101.0)), | 126.1     | 276      |
        | exit     | Waypoint((441.4, 101.6)), | 275.9     | 274      |
        """
        self.map_init(plane=Jarilo_BackwaterPass, floor="F1", position=(483.5, 105.1))
        self.register_domain_exit(Waypoint((441.4, 101.6)), end_rotation=274)
        enemy = Waypoint((457.4, 101.0))
        # ===== End of generated waypoints =====

        self.clear_enemy(enemy)

    def Jarilo_BackwaterPass_F1_X577Y665(self):
        """
        | Waypoint      | Position                  | Direction | Rotation |
        | ------------- | ------------------------- | --------- | -------- |
        | spawn         | Waypoint((577.4, 665.3)), | 139.7     | 140      |
        | event         | Waypoint((586.8, 680.2)), | 149.9     | 149      |
        | enemy3        | Waypoint((579.6, 732.2)), | 311.8     | 297      |
        | enemy1        | Waypoint((648.9, 714.7)), | 96.8      | 94       |
        | enemy2        | Waypoint((634.3, 748.5)), | 206.2     | 13       |
        | exit_X573Y720 | Waypoint((573.6, 720.6)), | 315.9     | 311      |
        """
        self.map_init(plane=Jarilo_BackwaterPass, floor="F1", position=(577.4, 665.3))
        self.register_domain_exit(Waypoint((573.6, 720.6)), end_rotation=311)
        event = Waypoint((586.8, 680.2))
        enemy3 = Waypoint((579.6, 732.2))
        enemy1 = Waypoint((648.9, 714.7))
        enemy2 = Waypoint((634.3, 748.5))
        # ===== End of generated waypoints =====

        self.clear_enemy(
            enemy1,
        )
        self.clear_enemy(
            enemy2.straight_run(),
        )
        self.clear_enemy(
            enemy3.straight_run(),
        )

    def Jarilo_BackwaterPass_F1_X580Y741(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((580.5, 741.2)), | 96.7      | 91       |
        | item     | Waypoint((621.4, 751.2)), | 129.8     | 124      |
        | enemy    | Waypoint((641.4, 743.1)), | 92.7      | 84       |
        | exit     | Waypoint((641.4, 743.1)), | 92.7      | 84       |
        """
        self.map_init(plane=Jarilo_BackwaterPass, floor="F1", position=(580.5, 741.2))
        self.register_domain_exit(Waypoint((641.4, 743.1)), end_rotation=84)
        item = Waypoint((621.4, 751.2))
        enemy = Waypoint((641.4, 743.1))
        # ===== End of generated waypoints =====

        # enemy first
        self.clear_enemy(enemy)
        self.clear_item(item)

    def Jarilo_BackwaterPass_F1_X595Y681(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((595.5, 681.5)), | 96.7      | 91       |
        | enemy    | Waypoint((631.8, 705.4)), | 134.2     | 91       |
        | exit     | Waypoint((635.5, 706.9)), | 129.9     | 126      |
        """
        self.map_init(plane=Jarilo_BackwaterPass, floor="F1", position=(595.5, 681.5))
        self.register_domain_exit(Waypoint((635.5, 706.9)), end_rotation=126)
        enemy = Waypoint((631.8, 705.4))
        # ===== End of generated waypoints =====

        self.clear_enemy(
            enemy.straight_run(),
        )
