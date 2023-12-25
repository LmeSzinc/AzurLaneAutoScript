from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Herta_SupplyZone
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Herta_SupplyZone_F2_X45Y369(self):
        """
        | Waypoint       | Position                  | Direction | Rotation |
        | -------------- | ------------------------- | --------- | -------- |
        | spawn          | Waypoint((45.5, 369.5)),  | 6.7       | 4        |
        | item1          | Waypoint((38.7, 346.8)),  | 36.0      | 359      |
        | door1          | Waypoint((46.6, 343.9)),  | 12.6      | 6        |
        | enemy1         | Waypoint((46.2, 328.2)),  | 12.6      | 8        |
        | item2          | Waypoint((42.4, 299.0)),  | 352.8     | 348      |
        | door2          | Waypoint((46.4, 284.5)),  | 4.2       | 1        |
        | enemy2left     | Waypoint((31.2, 248.8)),  | 183.8     | 84       |
        | enemy2right    | Waypoint((55.2, 247.2)),  | 96.7      | 91       |
        | item3          | Waypoint((68.5, 226.5)),  | 30.2      | 29       |
        | enemy3         | Waypoint((114.4, 234.7)), | 105.5     | 101      |
        | exit_          | Waypoint((119.1, 235.4)), | 6.8       | 96       |
        | exit1          | Waypoint((121.4, 229.4)), | 102.9     | 96       |
        | exit2_X121Y241 | Waypoint((121.7, 241.1)), | 99.1      | 354      |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2", position=(45.5, 369.5))
        self.register_domain_exit(
            Waypoint((119.1, 235.4)), end_rotation=96,
            left_door=Waypoint((121.4, 229.4)), right_door=Waypoint((121.7, 241.1)))
        item1 = Waypoint((38.7, 346.8))
        door1 = Waypoint((46.6, 343.9))
        enemy1 = Waypoint((46.2, 328.2))
        item2 = Waypoint((42.4, 299.0))
        door2 = Waypoint((46.4, 284.5))
        enemy2left = Waypoint((31.2, 248.8))
        enemy2right = Waypoint((55.2, 247.2))
        item3 = Waypoint((68.5, 226.5))
        enemy3 = Waypoint((114.4, 234.7))
        # ===== End of generated waypoints =====

        # 1, ignore item1, bad way
        self.clear_enemy(
            door1.set_threshold(3),
            enemy1,
        )
        # 2
        # self.clear_item(item2)
        self.clear_enemy(
            door2.set_threshold(3),
            # Go through door
            enemy2left,
            enemy2right.straight_run(),
        )
        # 3
        self.clear_item(
            item3.straight_run(),
        )
        self.clear_enemy(
            enemy3.straight_run(),
        )

    def Herta_SupplyZone_F2_X397Y233(self):
        """
        | Waypoint       | Position                  | Direction | Rotation |
        | -------------- | ------------------------- | --------- | -------- |
        | spawn          | Waypoint((397.4, 233.5)), | 6.7       | 4        |
        | item_X406Y202  | Waypoint((406.5, 202.1)), | 48.1      | 45       |
        | enemy_X397Y182 | Waypoint((397.2, 183.1)), | 356.3     | 4        |
        | exit_X397Y182  | Waypoint((397.2, 183.1)), | 356.3     | 4        |
        | exit1_X393Y163 | Waypoint((393.6, 163.7)), | 11.1      | 4        |
        | exit2_X406Y161 | Waypoint((406.6, 161.5)), | 4.3       | 357      |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2", position=(397.4, 233.5))
        self.register_domain_exit(
            Waypoint((397.2, 183.1)), end_rotation=4,
            left_door=Waypoint((393.6, 163.7)), right_door=Waypoint((406.6, 161.5)))
        item_X406Y202 = Waypoint((406.5, 202.1))
        enemy_X397Y182 = Waypoint((397.2, 183.1))
        # ===== End of generated waypoints =====

        # Ignore item, bad way
        self.clear_enemy(enemy_X397Y182)

    def Herta_SupplyZone_F2_X397Y239(self):
        """
        | Waypoint       | Position                  | Direction | Rotation |
        | -------------- | ------------------------- | --------- | -------- |
        | spawn          | Waypoint((397.4, 233.5)), | 6.7       | 4        |
        | item_X406Y202  | Waypoint((406.5, 202.1)), | 48.1      | 45       |
        | enemy_X397Y182 | Waypoint((397.2, 183.1)), | 356.3     | 4        |
        | exit_X397Y182  | Waypoint((397.2, 183.1)), | 356.3     | 4        |
        | exit1_X393Y163 | Waypoint((393.6, 163.7)), | 11.1      | 4        |
        | exit2_X406Y161 | Waypoint((406.6, 161.5)), | 4.3       | 357      |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2", position=(397.4, 239))
        self.register_domain_exit(
            Waypoint((397.2, 183.1)), end_rotation=4,
            left_door=Waypoint((393.6, 163.7)), right_door=Waypoint((406.6, 161.5)))
        item_X406Y202 = Waypoint((406.5, 202.1))
        enemy_X397Y182 = Waypoint((397.2, 183.1))
        # ===== End of generated waypoints =====

        # Ignore item, bad way
        self.clear_enemy(enemy_X397Y182)

        """
        Notes
        Herta_SupplyZone_F2_X397Y239 is the same as Herta_SupplyZone_F2_X397Y233
        but for wrong spawn point detected
        """

    def Herta_SupplyZone_F2_X543Y255(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((543.4, 255.2)), | 6.7       | 4        |
        | enemy1   | Waypoint((542.4, 163.0)), | 6.7       | 179      |
        | item1    | Waypoint((540.3, 136.6)), | 2.7       | 357      |
        | item2    | Waypoint((560.6, 132.9)), | 82.6      | 75       |
        | enemy2   | Waypoint((586.2, 128.9)), | 91.3      | 84       |
        | exit_    | Waypoint((588.4, 126.8)), | 5.7       | 1        |
        | exit1    | Waypoint((582.6, 124.4)), | 11.2      | 8        |
        | exit2    | Waypoint((594.2, 122.4)), | 14.1      | 8        |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2", position=(543.4, 255.2))
        self.register_domain_exit(
            Waypoint((588.4, 126.8)), end_rotation=1,
            left_door=Waypoint((582.6, 124.4)), right_door=Waypoint((594.2, 122.4)))
        enemy1 = Waypoint((542.4, 163.0))
        item1 = Waypoint((540.3, 136.6))
        item2 = Waypoint((560.6, 132.9))
        enemy2 = Waypoint((586.2, 128.9))
        # ===== End of generated waypoints =====

        self.clear_enemy(enemy1)
        self.clear_item(item1)
        self.clear_item(item2.straight_run())
        self.clear_enemy(enemy2)

    def Herta_SupplyZone_F2_X594Y247(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((594.3, 247.5)), | 274.2     | 274      |
        | item1    | Waypoint((578.9, 258.2)), | 282.8     | 276      |
        | enemy1   | Waypoint((542.2, 246.2)), | 302.7     | 301      |
        | enemy2   | Waypoint((542.2, 168.6)), | 11.1      | 177      |
        | enemy3   | Waypoint((586.5, 128.3)), | 87.7      | 260      |
        | item3    | Waypoint((560.2, 130.9)), | 67.2      | 66       |
        | exit_    | Waypoint((586.9, 129.8)), | 266.1     | 1        |
        | exit1    | Waypoint((580.9, 124.3)), | 354.1     | 350      |
        | exit2    | Waypoint((594.2, 122.2)), | 12.6      | 6        |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2", position=(594.3, 247.5))
        self.register_domain_exit(
            Waypoint((586.9, 129.8)), end_rotation=1,
            left_door=Waypoint((580.9, 124.3)), right_door=Waypoint((594.2, 122.2)))
        item1 = Waypoint((578.9, 258.2))
        enemy1 = Waypoint((542.2, 246.2))
        enemy2 = Waypoint((542.2, 168.6))
        enemy3 = Waypoint((586.5, 128.3))
        item3 = Waypoint((560.2, 130.9))
        # ===== End of generated waypoints =====

        self.clear_item(item1)
        self.clear_enemy(enemy1)
        self.clear_enemy(enemy2.straight_run())

        self.clear_item(
            # Go through enemy2 before turning right
            enemy2,
            item3.straight_run(),
        )
        self.clear_enemy(enemy3.straight_run())

    def Herta_SupplyZone_F2_X657Y247(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((656.7, 247.5)), | 274.2     | 274      |
        | item1    | Waypoint((578.9, 258.2)), | 282.8     | 276      |
        | enemy1   | Waypoint((542.2, 246.2)), | 302.7     | 301      |
        | enemy3   | Waypoint((586.5, 128.3)), | 87.7      | 260      |
        | enemy2   | Waypoint((542.2, 168.6)), | 11.1      | 177      |
        | item3    | Waypoint((560.2, 130.9)), | 67.2      | 66       |
        | exit_    | Waypoint((586.9, 129.8)), | 266.1     | 1        |
        | exit1    | Waypoint((580.8, 125.6)), | 101.3     | 1        |
        | exit2    | Waypoint((593.2, 123.5)), | 11.1      | 1        |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2", position=(656.7, 247.5))
        self.register_domain_exit(
            Waypoint((586.9, 129.8)), end_rotation=1,
            left_door=Waypoint((580.8, 125.6)), right_door=Waypoint((593.2, 123.5)))
        item1 = Waypoint((578.9, 258.2))
        enemy1 = Waypoint((542.2, 246.2))
        enemy3 = Waypoint((586.5, 128.3))
        enemy2 = Waypoint((542.2, 168.6))
        item3 = Waypoint((560.2, 130.9))
        # ===== End of generated waypoints =====

        """
        Notes
        Herta_SupplyZone_F2_X657Y247 is the same as Herta_SupplyZone_F2_X594Y247
        but for wrong spawn point detected
        """

        self.clear_item(item1)
        self.clear_enemy(enemy1)
        self.clear_enemy(enemy2.straight_run())

        self.clear_item(
            # Go through enemy2 before turning right
            enemy2,
            item3.straight_run(),
        )
        self.clear_enemy(enemy3.straight_run())
