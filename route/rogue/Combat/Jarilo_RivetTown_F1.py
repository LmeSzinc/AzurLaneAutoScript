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
        | item2        | Waypoint((130.4, 394.2)), | 12.7      | 6        |
        | enemy2       | Waypoint((118.4, 380.7)), | 61.1      | 308      |
        | enemy3       | Waypoint((58.4, 334.2)),  | 318.8     | 322      |
        | exit         | Waypoint((56.8, 332.4)),  | 333.0     | 329      |
        """
        self.map_init(plane=Jarilo_RivetTown, floor="F1", position=(181.4, 439.2))
        self.register_domain_exit(Waypoint((56.8, 332.4)), end_rotation=329)
        item1 = Waypoint((168.6, 430.8))
        enemy1middle = Waypoint((128.4, 440.0))
        item2 = Waypoint((130.4, 394.2))
        enemy2 = Waypoint((118.4, 380.7))
        enemy3 = Waypoint((58.4, 334.2))
        # ===== End of generated waypoints =====

        # 1
        self.clear_item(item1)
        self.clear_enemy(enemy1middle)
        # 2
        self.clear_item(
            item2.straight_run(),
        )
        self.clear_enemy(
            enemy2.straight_run(),
        )
        # 3
        self.clear_enemy(enemy3)

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

        self.clear_item(item)
        self.clear_enemy(enemy)

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
