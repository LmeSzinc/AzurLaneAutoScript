from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_ScalegorgeWaterscape
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_ScalegorgeWaterscape_F1_X467Y405(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((467.5, 405.5)), | 274.2     | 274      |
        | item     | Waypoint((444.6, 390.5)), | 20.4      | 18       |
        | node     | Waypoint((439.0, 388.5)), | 355.9     | 352      |
        | enemy1   | Waypoint((434.0, 406.2)), | 274.2     | 274      |
        | enemy2   | Waypoint((432.2, 367.2)), | 355.9     | 352      |
        | exit     | Waypoint((431.2, 363.2)), | 6.6       | 361      |
        """
        self.map_init(plane=Luofu_ScalegorgeWaterscape, floor="F1", position=(467.5, 405.5))
        self.register_domain_exit(Waypoint((431.2, 363.2)), end_rotation=361)
        item = Waypoint((444.6, 390.5))
        node = Waypoint((439.0, 388.5))
        enemy1 = Waypoint((434.0, 406.2))
        enemy2 = Waypoint((432.2, 367.2))
        # ===== End of generated waypoints =====

        # Ignore item at the corner
        self.clear_enemy(enemy1)
        self.clear_enemy(enemy2.straight_run())

    def Luofu_ScalegorgeWaterscape_F1_X617Y99(self):
        """
        | Waypoint | Position                 | Direction | Rotation |
        | -------- | ------------------------ | --------- | -------- |
        | spawn    | Waypoint((617.3, 99.4)), | 6.7       | 361      |
        | item     | Waypoint((610.5, 88.6)), | 337.2     | 334      |
        | enemy    | Waypoint((616.2, 64.4)), | 22.7      | 195      |
        | exit     | Waypoint((617.2, 66.6)), | 12.6      | 4        |
        """
        self.map_init(plane=Luofu_ScalegorgeWaterscape, floor="F1", position=(617.3, 99.4))
        self.register_domain_exit(Waypoint((617.2, 66.6)), end_rotation=4)
        item = Waypoint((610.5, 88.6))
        enemy = Waypoint((616.2, 64.4))
        # ===== End of generated waypoints =====

        self.clear_item(item)
        self.clear_enemy(enemy)

    def Luofu_ScalegorgeWaterscape_F1_X668Y243(self):
        """
        | Waypoint       | Position                  | Direction | Rotation |
        | -------------- | ------------------------- | --------- | -------- |
        | spawn          | Waypoint((668.9, 243.4)), | 96.7      | 91       |
        | item           | Waypoint((690.8, 236.8)), | 45.8      | 43       |
        | enemy_X701Y242 | Waypoint((701.6, 242.2)), | 98.0      | 89       |
        | exit_X701Y242  | Waypoint((701.6, 242.2)), | 98.0      | 89       |
        """
        self.map_init(plane=Luofu_ScalegorgeWaterscape, floor="F1", position=(668.9, 243.4))
        self.register_domain_exit(Waypoint((701.6, 242.2)), end_rotation=89)
        item = Waypoint((690.8, 236.8))
        enemy_X701Y242 = Waypoint((701.6, 242.2))
        # ===== End of generated waypoints =====

        # Ignore item, too close to enemy
        self.clear_enemy(enemy_X701Y242)

    def Luofu_ScalegorgeWaterscape_F1_X1181Y279(self):
        """
        | Waypoint | Position                   | Direction | Rotation |
        | -------- | -------------------------- | --------- | -------- |
        | spawn    | Waypoint((1181.0, 279.5)), | 274.2     | 274      |
        | enemy1   | Waypoint((1160.6, 273.0)), | 294.5     | 290      |
        | item1    | Waypoint((1161.2, 288.6)), | 262.6     | 255      |
        | item3    | Waypoint((1125.2, 274.6)), | 12.7      | 4        |
        | enemy2   | Waypoint((1128.4, 298.8)), | 241.2     | 253      |
        | item2    | Waypoint((1125.0, 290.7)), | 352.8     | 359      |
        | enemy4   | Waypoint((1091.8, 280.2)), | 275.8     | 276      |
        | exit     | Waypoint((1090.7, 280.4)), | 282.8     | 274      |
        """
        self.map_init(plane=Luofu_ScalegorgeWaterscape, floor="F1", position=(1181.0, 279.5))
        self.register_domain_exit(Waypoint((1090.7, 280.4)), end_rotation=274)
        enemy1 = Waypoint((1160.6, 273.0))
        item1 = Waypoint((1161.2, 288.6))
        item3 = Waypoint((1125.2, 274.6))
        enemy2 = Waypoint((1128.4, 298.8))
        item2 = Waypoint((1125.0, 290.7))
        enemy4 = Waypoint((1091.8, 280.2))
        # ===== End of generated waypoints =====

        # Ignore items and enemy2, as it's a straight way to exit
        self.clear_enemy(enemy1)
        self.clear_enemy(enemy4)
