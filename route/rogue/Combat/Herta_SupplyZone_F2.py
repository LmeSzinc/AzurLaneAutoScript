from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Herta_SupplyZone
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Herta_SupplyZone_F2_X215Y112(self):
        """
        | Waypoint      | Position                  | Direction | Rotation |
        | ------------- | ------------------------- | --------- | -------- |
        | spawn         | Waypoint((215.6, 112.7)), | 96.7      | 91       |
        | item_X227Y105 | Waypoint((227.4, 105.0)), | 67.2      | 61       |
        | enemy         | Waypoint((264.4, 114.1)), | 101.1     | 98       |
        | exit_X227Y105 | Waypoint((266.7, 113.7)), | 60.8      | 91       |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2", position=(215.6, 112.7))
        self.register_domain_exit(Waypoint((266.7, 113.7)), end_rotation=91)
        item_X227Y105 = Waypoint((227.4, 105.0))
        enemy = Waypoint((264.4, 114.1))
        # ===== End of generated waypoints =====

        self.clear_item(item_X227Y105)
        self.clear_enemy(enemy)

    def Herta_SupplyZone_F2_X45Y369(self):
        """
        | Waypoint            | Position                  | Direction | Rotation |
        | ------------------- | ------------------------- | --------- | -------- |
        | spawn               | Waypoint((45.5, 369.5)),  | 6.7       | 4        |
        | item1               | Waypoint((38.7, 346.8)),  | 36.0      | 359      |
        | enemy1              | Waypoint((44.2, 328.8)),  | 6.7       | 4        |
        | item2               | Waypoint((34.4, 299.0)),  | 352.8     | 348      |
        | door2               | Waypoint((46.4, 284.5)),  | 4.2       | 361      |
        | enemy2left_X31Y248  | Waypoint((31.2, 248.8)),  | 183.8     | 84       |
        | enemy2right_X55Y247 | Waypoint((55.2, 247.2)),  | 96.7      | 91       |
        | item3               | Waypoint((68.5, 226.5)),  | 30.2      | 29       |
        | enemy3_X114Y234     | Waypoint((114.4, 234.7)), | 105.5     | 101      |
        | exit_X116Y228       | Waypoint((116.6, 228.8)), | 96.8      | 94       |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2", position=(45.5, 369.5))
        self.register_domain_exit(Waypoint((116.6, 228.8)), end_rotation=94)
        item1 = Waypoint((38.7, 346.8))
        enemy1 = Waypoint((44.2, 328.8))
        item2 = Waypoint((34.4, 299.0))
        door2 = Waypoint((46.4, 284.5))
        enemy2left_X31Y248 = Waypoint((31.2, 248.8))
        enemy2right_X55Y247 = Waypoint((55.2, 247.2))
        item3 = Waypoint((68.5, 226.5))
        enemy3_X114Y234 = Waypoint((114.4, 234.7))
        # ===== End of generated waypoints =====

        # 1, ignore item1, bad way
        self.clear_enemy(enemy1)
        # 2
        self.clear_item(item2)
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
