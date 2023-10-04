from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_RivetTown
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_RivetTown_F1_X181Y439(self):
        """
        | Waypoint     | Position                  | Direction | Rotation |
        | ------------ | ------------------------- | --------- | -------- |
        | spawn        | Waypoint((181.4, 439.2)), | 274.2     | 274      |
        | item1        | Waypoint((168.6, 430.8)), | 311.8     | 308      |
        | enemy1middle | Waypoint((128.4, 440.0)), | 275.8     | 82       |
        | node2        | Waypoint((126.2, 425.6)), | 188.9     | 4        |
        | item2        | Waypoint((130.4, 394.2)), | 12.7      | 6        |
        | enemy2       | Waypoint((118.4, 380.7)), | 61.1      | 308      |
        | enemy3       | Waypoint((58.4, 334.2)),  | 318.8     | 322      |
        | exit         | Waypoint((56.8, 332.4)),  | 333.0     | 329      |
        """
        self.map_init(plane=Jarilo_RivetTown, floor="F1", position=(181.4, 439.2))
        self.register_domain_exit(Waypoint((56.8, 332.4)), end_rotation=329)
        item1 = Waypoint((168.6, 430.8))
        enemy1middle = Waypoint((128.4, 440.0))
        node2 = Waypoint((126.2, 425.6))
        item2 = Waypoint((130.4, 394.2))
        enemy2 = Waypoint((118.4, 380.7))
        enemy3 = Waypoint((58.4, 334.2))
        # ===== End of generated waypoints =====

        # 1
        self.clear_item(item1)
        self.clear_enemy(enemy1middle)
        # 2
        self.clear_item(
            node2,
            item2.straight_run(),
        )
        self.clear_enemy(
            enemy2.straight_run(),
        )
        # 3
        self.clear_enemy(enemy3)

    def Jarilo_RivetTown_F1_X205Y439(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((205.4, 439.5)), | 274.2     | 274      |
        | item     | Waypoint((168.6, 430.8)), | 311.8     | 308      |
        | enemy    | Waypoint((137.0, 438.1)), | 96.7      | 274      |
        | exit     | Waypoint((137.0, 438.1)), | 96.7      | 274      |
        """
        self.map_init(plane=Jarilo_RivetTown, floor="F1", position=(205.4, 439.5))
        self.register_domain_exit(Waypoint((137.0, 438.1)), end_rotation=274)
        item = Waypoint((168.6, 430.8))
        enemy = Waypoint((137.0, 438.1))
        # ===== End of generated waypoints =====

        self.clear_item(item)
        self.clear_enemy(enemy)

    def Jarilo_RivetTown_F1_X209Y333(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((209.4, 333.5)), | 190.1     | 181      |
        | item     | Waypoint((222.6, 371.5)), | 166.7     | 165      |
        | enemy    | Waypoint((206.2, 387.8)), | 190.1     | 191      |
        | exit     | Waypoint((209.2, 392.8)), | 189.0     | 184      |
        """
        self.map_init(plane=Jarilo_RivetTown, floor="F1", position=(209.4, 333.5))
        self.register_domain_exit(Waypoint((209.2, 392.8)), end_rotation=184)
        item = Waypoint((222.6, 371.5))
        enemy = Waypoint((206.2, 387.8))
        # ===== End of generated waypoints =====

        # Ignore item, too close to enemy
        # self.clear_item(item)
        self.clear_enemy(enemy)

    def Jarilo_RivetTown_F1_X231Y211(self):
        """
        | Waypoint     | Position                  | Direction | Rotation |
        | ------------ | ------------------------- | --------- | -------- |
        | spawn        | Waypoint((231.4, 211.1)), | 30.1      | 27       |
        | item1        | Waypoint((236.7, 180.5)), | 25.6      | 22       |
        | node2        | Waypoint((256.9, 180.9)), | 182.9     | 84       |
        | enemy1       | Waypoint((256.6, 169.0)), | 36.3      | 211      |
        | item2        | Waypoint((280.5, 188.5)), | 114.2     | 110      |
        | enemy2middle | Waypoint((290.0, 174.6)), | 92.7      | 84       |
        | enemy3       | Waypoint((319.6, 153.1)), | 76.4      | 73       |
        | exit         | Waypoint((317.4, 155.3)), | 60.9      | 73       |
        """
        self.map_init(plane=Jarilo_RivetTown, floor="F1", position=(231.4, 211.1))
        self.register_domain_exit(Waypoint((317.4, 155.3)), end_rotation=73)
        item1 = Waypoint((236.7, 180.5))
        node2 = Waypoint((256.9, 180.9))
        enemy1 = Waypoint((256.6, 169.0))
        item2 = Waypoint((280.5, 188.5))
        enemy2middle = Waypoint((290.0, 174.6))
        enemy3 = Waypoint((319.6, 153.1))
        # ===== End of generated waypoints =====

        self.rotation_set(73)
        # Ignore all items, road blocked
        self.clear_enemy(enemy1)
        self.clear_enemy(
            node2,
            enemy2middle
        )
        self.clear_enemy(enemy3)

    def Jarilo_RivetTown_F1_X279Y301(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((279.4, 301.6)), | 36.1      | 31       |
        | item     | Waypoint((302.6, 270.6)), | 59.1      | 54       |
        | enemy    | Waypoint((298.2, 246.0)), | 36.2      | 36       |
        | exit     | Waypoint((298.2, 246.0)), | 36.2      | 36       |
        """
        self.map_init(plane=Jarilo_RivetTown, floor="F1", position=(279.4, 301.6))
        self.register_domain_exit(Waypoint((298.2, 246.0)), end_rotation=36)
        item = Waypoint((302.6, 270.6))
        enemy = Waypoint((298.2, 246.0))
        # ===== End of generated waypoints =====

        self.clear_item(item)
        self.clear_enemy(enemy)

    def Jarilo_RivetTown_F1_X293Y243(self):
        """
        | Waypoint    | Position                  | Direction | Rotation |
        | ----------- | ------------------------- | --------- | -------- |
        | spawn       | Waypoint((293.6, 243.5)), | 182.9     | 177      |
        | item1       | Waypoint((302.5, 259.5)), | 175.8     | 168      |
        | enemy1right | Waypoint((290.0, 276.0)), | 198.7     | 195      |
        | enemy1left  | Waypoint((310.1, 281.1)), | 105.5     | 101      |
        | item2       | Waypoint((326.2, 298.0)), | 151.8     | 140      |
        | enemy2      | Waypoint((318.6, 334.8)), | 195.2     | 6        |
        | enemy3      | Waypoint((316.4, 385.0)), | 223.8     | 45       |
        | exit        | Waypoint((314.6, 385.0)), | 289.0     | 188      |
        """
        self.map_init(plane=Jarilo_RivetTown, floor="F1", position=(293.6, 243.5))
        self.register_domain_exit(Waypoint((314.6, 385.0)), end_rotation=188)
        item1 = Waypoint((302.5, 259.5))
        enemy1right = Waypoint((290.0, 276.0))
        enemy1left = Waypoint((310.1, 281.1))
        item2 = Waypoint((326.2, 298.0))
        enemy2 = Waypoint((318.6, 334.8))
        enemy3 = Waypoint((316.4, 385.0))
        # ===== End of generated waypoints =====

        # 1, ignore item1
        self.clear_enemy(
            enemy1right,
            enemy1left.straight_run(),
        )
        # 2
        self.clear_item(
            item2.straight_run(),
        )
        self.clear_enemy(
            enemy2.straight_run(),
        )
        # 3
        self.clear_enemy(
            enemy3,
        )

    def Jarilo_RivetTown_F1_X323Y151(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((323.4, 151.5)), | 257.0     | 253      |
        | item1    | Waypoint((298.4, 150.8)), | 282.7     | 278      |
        | enemy1   | Waypoint((260.2, 184.6)), | 241.2     | 239      |
        | item2    | Waypoint((240.4, 178.8)), | 276.0     | 274      |
        | enemy2   | Waypoint((234.6, 204.8)), | 315.9     | 209      |
        | exit     | Waypoint((234.6, 204.8)), | 315.9     | 209      |
        """
        self.map_init(plane=Jarilo_RivetTown, floor="F1", position=(323.4, 151.5))
        self.register_domain_exit(Waypoint((234.6, 204.8)), end_rotation=209)
        item1 = Waypoint((298.4, 150.8))
        enemy1 = Waypoint((260.2, 184.6))
        item2 = Waypoint((240.4, 178.8))
        enemy2 = Waypoint((234.6, 204.8))
        # ===== End of generated waypoints =====

        self.clear_item(item1)
        self.clear_enemy(enemy1)
        # Ignore item2, position blocked
        self.clear_enemy(enemy2.straight_run())
