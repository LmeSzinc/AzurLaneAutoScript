from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_StargazerNavalia
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

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
