from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Herta_SupplyZone
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Herta_SupplyZone_F2_X45Y369(self):
        """
        | Waypoint            | Position                  | Direction | Rotation |
        | ------------------- | ------------------------- | --------- | -------- |
        | spawn               | Waypoint((45.5, 369.5)),  | 6.7       | 4        |
        | item1               | Waypoint((38.7, 346.8)),  | 36.0      | 359      |
        | door1               | Waypoint((46.6, 343.9)),  | 12.6      | 6        |
        | enemy1              | Waypoint((46.2, 328.2)),  | 12.6      | 8        |
        | item2               | Waypoint((34.4, 299.0)),  | 352.8     | 348      |
        | door2               | Waypoint((46.4, 284.5)),  | 4.2       | 361      |
        | enemy2left_X31Y248  | Waypoint((31.2, 248.8)),  | 183.8     | 84       |
        | enemy2right_X55Y247 | Waypoint((55.2, 247.2)),  | 96.7      | 91       |
        | item3               | Waypoint((68.5, 226.5)),  | 30.2      | 29       |
        | enemy3_X114Y234     | Waypoint((114.4, 234.7)), | 105.5     | 101      |
        | exit                | Waypoint((119.1, 235.4)), | 6.8       | 96       |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2", position=(45.5, 369.5))
        self.register_domain_exit(Waypoint((119.1, 235.4)), end_rotation=96)
        item1 = Waypoint((38.7, 346.8))
        door1 = Waypoint((46.6, 343.9))
        enemy1 = Waypoint((46.2, 328.2))
        item2 = Waypoint((34.4, 299.0))
        door2 = Waypoint((46.4, 284.5))
        enemy2left_X31Y248 = Waypoint((31.2, 248.8))
        enemy2right_X55Y247 = Waypoint((55.2, 247.2))
        item3 = Waypoint((68.5, 226.5))
        enemy3_X114Y234 = Waypoint((114.4, 234.7))
        # ===== End of generated waypoints =====

        # 1, ignore item1, bad way
        self.clear_enemy(
            door1.set_threshold(3),
            enemy1,
        )
        # 2
        # self.clear_item(item2)
        self.clear_enemy(
            door2,
            enemy2left_X31Y248.straight_run(),
            enemy2right_X55Y247.straight_run(),
        )
        # 3
        self.clear_item(
            item3.straight_run(),
        )
        self.clear_enemy(
            enemy3_X114Y234.straight_run(),
        )

    def Herta_SupplyZone_F2_X397Y233(self):
        """
        | Waypoint       | Position                  | Direction | Rotation |
        | -------------- | ------------------------- | --------- | -------- |
        | spawn          | Waypoint((397.4, 233.5)), | 6.7       | 4        |
        | item_X406Y202  | Waypoint((406.5, 202.1)), | 48.1      | 45       |
        | enemy_X397Y182 | Waypoint((397.2, 183.1)), | 356.3     | 4        |
        | exit_X397Y182  | Waypoint((397.2, 183.1)), | 356.3     | 4        |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2", position=(397.4, 233.5))
        self.register_domain_exit(Waypoint((397.2, 183.1)), end_rotation=4)
        item_X406Y202 = Waypoint((406.5, 202.1))
        enemy_X397Y182 = Waypoint((397.2, 183.1))
        # ===== End of generated waypoints =====

        # Ignore item, bad way
        self.clear_enemy(enemy_X397Y182)

    def Herta_SupplyZone_F2_X658Y247(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((656.7, 247.5)), | 274.2     | 274      |
        | item1    | Waypoint((664.9, 264.2)), | 282.8     | 276      |
        | enemy1   | Waypoint((542.2, 246.2)), | 302.7     | 301      |
        | enemy3   | Waypoint((586.5, 128.3)), | 87.7      | 260      |
        | enemy2   | Waypoint((542.2, 168.6)), | 11.1      | 177      |
        | item3    | Waypoint((564.2, 130.9)), | 67.2      | 66       |
        | exit     | Waypoint((586.9, 135.8)), | 266.1     | 361      |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2", position=(656.7, 247.5))
        self.register_domain_exit(Waypoint((586.9, 135.8)), end_rotation=361)
        item1 = Waypoint((664.9, 264.2))
        enemy1 = Waypoint((542.2, 246.2))
        enemy3 = Waypoint((586.5, 128.3))
        enemy2 = Waypoint((542.2, 168.6))
        item3 = Waypoint((564.2, 130.9))
        # ===== End of generated waypoints =====

        self.clear_item(item1)
        self.clear_enemy(enemy1)
        self.clear_enemy(enemy2.straight_run())

        self.clear_item(item3.straight_run())
        self.clear_enemy(enemy3.straight_run())
