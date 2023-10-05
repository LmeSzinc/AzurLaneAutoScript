from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_Cloudford
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_Cloudford_F1Rogue_X49Y405(self):
        """
        | Waypoint              | Position                  | Direction | Rotation |
        | --------------------- | ------------------------- | --------- | -------- |
        | spawn                 | Waypoint((49.3, 405.6)),  | 96.7      | 91       |
        | item1                 | Waypoint((96.9, 393.0)),  | 87.7      | 84       |
        | enemy1_X126Y402       | Waypoint((126.2, 402.5)), | 96.8      | 101      |
        | node2                 | Waypoint((142.9, 413.0)), | 96.8      | 101      |
        | enemy2top             | Waypoint((214.6, 432.8)), | 94.1      | 87       |
        | enemy2bottom_X212Y483 | Waypoint((211.4, 483.3)), | 191.8     | 174      |
        | enemy3                | Waypoint((288.0, 452.2)), | 87.7      | 260      |
        | exit_X288Y454         | Waypoint((291.8, 454.4)), | 5.7       | 91       |
        """
        self.map_init(plane=Luofu_Cloudford, floor="F1Rogue", position=(49.3, 405.6))
        self.register_domain_exit(Waypoint((291.8, 454.4)), end_rotation=91)
        item1 = Waypoint((96.9, 393.0))
        enemy1_X126Y402 = Waypoint((126.2, 402.5))
        node2 = Waypoint((142.9, 413.0))
        enemy2top = Waypoint((214.6, 432.8))
        enemy2bottom_X212Y483 = Waypoint((211.4, 483.3))
        enemy3 = Waypoint((288.0, 452.2))
        # ===== End of generated waypoints =====

        # 1, ignore item1, which position may cause detection error
        # self.clear_item(item1)
        self.clear_enemy(enemy1_X126Y402)
        # 2 moving enemy
        # Ignore enemy2, it might be a pig, you can never catch it.
        # self.clear_enemy(
        #     enemy2top,
        #     enemy2bottom.straight_run(),
        # )
        # 3
        self.clear_enemy(
            node2.set_threshold(3),
            enemy3.straight_run(),
        )
