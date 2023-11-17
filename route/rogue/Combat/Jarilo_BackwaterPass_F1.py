from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_BackwaterPass
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_BackwaterPass_F1_X460Y165(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((460.0, 165.3)), | 146.7     | 140      |
        | item1    | Waypoint((478.0, 165.1)), | 101.2     | 101      |
        | enemy1   | Waypoint((492.8, 194.9)), | 227.8     | 133      |
        | enemy2   | Waypoint((512.8, 216.6)), | 146.6     | 140      |
        | exit_    | Waypoint((512.8, 216.6)), | 146.6     | 140      |
        | exit1    | Waypoint((521.4, 215.6)), | 135.8     | 131      |
        | exit2    | Waypoint((510.4, 222.4)), | 151.8     | 142      |
        """
        self.map_init(plane=Jarilo_BackwaterPass, floor="F1", position=(460.0, 165.3))
        self.register_domain_exit(
            Waypoint((512.8, 216.6)), end_rotation=140,
            left_door=Waypoint((521.4, 215.6)), right_door=Waypoint((510.4, 222.4)))
        item1 = Waypoint((478.0, 165.1))
        enemy1 = Waypoint((492.8, 194.9))
        enemy2 = Waypoint((512.8, 216.6))
        # ===== End of generated waypoints =====

        self.clear_item(item1)
        self.clear_enemy(enemy1)
        self.clear_enemy(enemy2)

    def Jarilo_BackwaterPass_F1_X475Y49(self):
        """
        | Waypoint    | Position                  | Direction | Rotation |
        | ----------- | ------------------------- | --------- | -------- |
        | spawn       | Waypoint((475.2, 49.5)),  | 190.1     | 184      |
        | enemy1left  | Waypoint((475.6, 99.4)),  | 30.1      | 184      |
        | enemy1right | Waypoint((451.5, 103.2)), | 277.2     | 274      |
        | node2       | Waypoint((456.2, 110.4)), | 290.2     | 186      |
        | enemy2      | Waypoint((464.2, 168.0)), | 166.8     | 341      |
        | enemy3      | Waypoint((500.9, 202.8)), | 135.8     | 133      |
        | exit_       | Waypoint((500.9, 202.8)), | 135.8     | 133      |
        | exit1       | Waypoint((511.2, 201.2)), | 148.4     | 140      |
        | exit2       | Waypoint((501.0, 212.0)), | 148.8     | 140      |
        """
        self.map_init(plane=Jarilo_BackwaterPass, floor="F1", position=(475.2, 49.5))
        self.register_domain_exit(
            Waypoint((500.9, 202.8)), end_rotation=133,
            left_door=Waypoint((511.2, 201.2)), right_door=Waypoint((501.0, 212.0)))
        enemy1left = Waypoint((475.6, 99.4))
        enemy1right = Waypoint((451.5, 103.2))
        node2 = Waypoint((456.2, 110.4))
        enemy2 = Waypoint((464.2, 168.0))
        enemy3 = Waypoint((500.9, 202.8))
        # ===== End of generated waypoints =====

        # 1
        self.rotation_set(225)
        self.clear_enemy(
            enemy1left,
            enemy1right,
        )
        # 2
        self.clear_enemy(
            node2,
            enemy2.straight_run(),
        )
        # 3
        self.clear_enemy(
            enemy2,
            enemy3.straight_run(),
        )

    def Jarilo_BackwaterPass_F1_X483Y105(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((483.5, 105.1)), | 275.8     | 87       |
        | enemy    | Waypoint((457.4, 101.0)), | 126.1     | 276      |
        | exit_    | Waypoint((441.4, 101.6)), | 275.9     | 274      |
        """
        self.map_init(plane=Jarilo_BackwaterPass, floor="F1", position=(483.5, 105.1))
        self.register_domain_exit(Waypoint((441.4, 101.6)), end_rotation=274)
        enemy = Waypoint((457.4, 101.0))
        # ===== End of generated waypoints =====

        self.clear_enemy(enemy)

    def Jarilo_BackwaterPass_F1_X507Y733(self):
        """
        | Waypoint   | Position                  | Direction | Rotation |
        | ---------- | ------------------------- | --------- | -------- |
        | spawn      | Waypoint((507.2, 733.7)), | 6.7       | 4        |
        | enemy1     | Waypoint((507.0, 644.0)), | 12.6      | 6        |
        | enemy2left | Waypoint((536.0, 630.5)), | 48.1      | 43       |
        | enemy3     | Waypoint((557.0, 585.2)), | 114.1     | 6        |
        | exit_      | Waypoint((557.0, 585.2)), | 114.1     | 6        |
        """
        self.map_init(plane=Jarilo_BackwaterPass, floor="F1", position=(507.2, 733.7))
        self.register_domain_exit(Waypoint((557.0, 585.2)), end_rotation=6)
        enemy1 = Waypoint((507.0, 644.0))
        enemy2left = Waypoint((536.0, 630.5))
        enemy3 = Waypoint((557.0, 585.2))
        # ===== End of generated waypoints =====

        self.clear_enemy(enemy1)
        self.clear_enemy(enemy2left.straight_run())
        self.clear_enemy(enemy3.straight_run())

    def Jarilo_BackwaterPass_F1_X555Y643(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((555.6, 643.2)), | 282.3     | 274      |
        | item     | Waypoint((524.8, 620.4)), | 318.0     | 322      |
        | enemy    | Waypoint((505.7, 642.9)), | 14.1      | 274      |
        | exit_    | Waypoint((505.3, 643.3)), | 180.1     | 274      |
        | exit1    | Waypoint((501.2, 648.6)), | 275.9     | 274      |
        | exit2    | Waypoint((501.5, 633.9)), | 281.9     | 274      |
        """
        self.map_init(plane=Jarilo_BackwaterPass, floor="F1", position=(555.6, 643.2))
        self.register_domain_exit(
            Waypoint((505.3, 643.3)), end_rotation=274,
            left_door=Waypoint((501.2, 648.6)), right_door=Waypoint((501.5, 633.9)))
        item = Waypoint((524.8, 620.4))
        enemy = Waypoint((505.7, 642.9))
        # ===== End of generated waypoints =====

        self.clear_item(item)
        self.clear_enemy(enemy)

    def Jarilo_BackwaterPass_F1_X577Y665(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((577.4, 665.3)), | 139.7     | 140      |
        | event    | Waypoint((586.8, 680.2)), | 149.9     | 149      |
        | enemy3   | Waypoint((579.6, 732.2)), | 311.8     | 297      |
        | enemy1   | Waypoint((648.9, 714.7)), | 96.8      | 94       |
        | enemy2   | Waypoint((634.3, 748.5)), | 206.2     | 13       |
        | exit_    | Waypoint((577.6, 728.6)), | 315.9     | 311      |
        | exit1    | Waypoint((564.2, 732.2)), | 311.8     | 308      |
        | exit2    | Waypoint((574.8, 722.4)), | 311.8     | 308      |
        """
        self.map_init(plane=Jarilo_BackwaterPass, floor="F1", position=(577.4, 665.3))
        self.register_domain_exit(
            Waypoint((577.6, 728.6)), end_rotation=311,
            left_door=Waypoint((564.2, 732.2)), right_door=Waypoint((574.8, 722.4)))
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
        | exit_    | Waypoint((641.4, 743.1)), | 92.7      | 84       |
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
        | exit_    | Waypoint((635.5, 706.9)), | 129.9     | 126      |
        | exit1    | Waypoint((647.4, 705.3)), | 119.8     | 121      |
        | exit2    | Waypoint((639.3, 715.4)), | 135.8     | 131      |
        """
        self.map_init(plane=Jarilo_BackwaterPass, floor="F1", position=(595.5, 681.5))
        self.register_domain_exit(
            Waypoint((635.5, 706.9)), end_rotation=126,
            left_door=Waypoint((647.4, 705.3)), right_door=Waypoint((639.3, 715.4)))
        enemy = Waypoint((631.8, 705.4))
        # ===== End of generated waypoints =====

        self.clear_enemy(
            enemy.straight_run(),
        )
