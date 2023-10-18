from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_StargazerNavalia
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_StargazerNavalia_F2_X479Y187(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((479.5, 187.5)), | 94.3      | 94       |
        | item1    | Waypoint((516.4, 194.2)), | 94.3      | 91       |
        | enemy1   | Waypoint((538.2, 182.6)), | 94.5      | 94       |
        | enemy2   | Waypoint((572.4, 180.2)), | 284.6     | 94       |
        | node3    | Waypoint((618.0, 182.4)), | 274.2     | 105      |
        | enemy3   | Waypoint((622.2, 170.0)), | 284.7     | 94       |
        | exit     | Waypoint((619.5, 169.4)), | 193.0     | 6        |
        """
        self.map_init(plane=Luofu_StargazerNavalia, floor="F2", position=(479.5, 187.5))
        self.register_domain_exit(Waypoint((619.5, 169.4)), end_rotation=6)
        item1 = Waypoint((516.4, 194.2))
        enemy1 = Waypoint((538.2, 182.6))
        enemy2 = Waypoint((572.4, 180.2))
        node3 = Waypoint((618.0, 182.4))
        enemy3 = Waypoint((622.2, 170.0))
        # ===== End of generated waypoints =====

        self.clear_item(item1)
        self.clear_enemy(enemy1)
        # Go through enemy1 on the bridge
        self.clear_enemy(
            enemy1.set_threshold(3),
            enemy2,
        )
        self.rotation_set(60)
        self.clear_enemy(
            node3,
            enemy3,
        )

    def Luofu_StargazerNavalia_F2_X627Y179(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((627.8, 179.5)), | 274.2     | 274      |
        | item1    | Waypoint((574.0, 172.5)), | 303.8     | 304      |
        | enemy1   | Waypoint((571.9, 180.5)), | 282.8     | 276      |
        | item2    | Waypoint((504.8, 177.2)), | 283.0     | 278      |
        | enemy2   | Waypoint((488.6, 188.2)), | 282.3     | 274      |
        | exit     | Waypoint((486.5, 191.4)), | 182.7     | 274      |
        """
        self.map_init(plane=Luofu_StargazerNavalia, floor="F2", position=(627.8, 179.5))
        self.register_domain_exit(Waypoint((486.5, 191.4)), end_rotation=274)
        item1 = Waypoint((574.0, 172.5))
        enemy1 = Waypoint((571.9, 180.5))
        item2 = Waypoint((504.8, 177.2))
        enemy2 = Waypoint((488.6, 188.2))
        # ===== End of generated waypoints =====

        # 1, enemy first
        self.clear_enemy(enemy1)
        self.clear_item(item1)
        # 2, ignore item2, bad way
        self.clear_enemy(enemy2)
