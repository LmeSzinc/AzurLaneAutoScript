from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_ScalegorgeWaterscape
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_ScalegorgeWaterscape_F1_X415Y261(self):
        """
        | Waypoint    | Position                  | Direction | Rotation |
        | ----------- | ------------------------- | --------- | -------- |
        | spawn       | Waypoint((415.4, 261.6)), | 274.2     | 274      |
        | item1       | Waypoint((396.6, 270.2)), | 250.8     | 251      |
        | enemy1right | Waypoint((385.0, 274.4)), | 250.7     | 248      |
        | node2       | Waypoint((381.0, 281.0)), | 283.0     | 278      |
        | enemy1left  | Waypoint((384.2, 292.0)), | 12.7      | 186      |
        | enemy2      | Waypoint((340.2, 281.8)), | 275.8     | 87       |
        | enemy3      | Waypoint((283.6, 280.0)), | 282.7     | 276      |
        | exit        | Waypoint((278.4, 280.2)), | 274.2     | 271      |
        """
        self.map_init(plane=Luofu_ScalegorgeWaterscape, floor="F1", position=(415.4, 261.6))
        self.register_domain_exit(Waypoint((278.4, 280.2)), end_rotation=271)
        item1 = Waypoint((396.6, 270.2))
        enemy1right = Waypoint((385.0, 274.4))
        node2 = Waypoint((381.0, 281.0))
        enemy1left = Waypoint((384.2, 292.0))
        enemy2 = Waypoint((340.2, 281.8))
        enemy3 = Waypoint((283.6, 280.0))
        # ===== End of generated waypoints =====

        self.rotation_set(245)
        self.minimap.lock_rotation(245)
        self.clear_item(item1)
        self.clear_enemy(
            enemy1right,
            enemy1left,
        )
        self.minimap.init_position(self.minimap.position)
        self.rotation_set(270)
        self.minimap.lock_rotation(270)
        self.clear_enemy(
            node2,
            enemy2,
        )
        self.clear_enemy(enemy3)

    def Luofu_ScalegorgeWaterscape_F1_X467Y405(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((467.5, 405.5)), | 274.2     | 274      |
        | item     | Waypoint((444.6, 390.5)), | 20.4      | 18       |
        | node     | Waypoint((439.0, 388.5)), | 355.9     | 352      |
        | enemy1   | Waypoint((434.0, 406.2)), | 274.2     | 274      |
        | enemy2   | Waypoint((432.2, 367.2)), | 355.9     | 352      |
        | exit     | Waypoint((431.2, 363.2)), | 6.6       | 1        |
        """
        self.map_init(plane=Luofu_ScalegorgeWaterscape, floor="F1", position=(467.5, 405.5))
        self.register_domain_exit(Waypoint((431.2, 363.2)), end_rotation=1)
        item = Waypoint((444.6, 390.5))
        node = Waypoint((439.0, 388.5))
        enemy1 = Waypoint((434.0, 406.2))
        enemy2 = Waypoint((432.2, 367.2))
        # ===== End of generated waypoints =====

        # Ignore item at the corner
        self.clear_enemy(enemy1)
        self.clear_enemy(enemy2.straight_run())

    def Luofu_ScalegorgeWaterscape_F1_X567Y280(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((567.4, 280.2)), | 274.2     | 274      |
        | enemy1   | Waypoint((495.3, 273.7)), | 219.9     | 292      |
        | node2    | Waypoint((482.8, 252.6)), | 337.3     | 336      |
        | enemy2   | Waypoint((485.0, 211.7)), | 17.3      | 15       |
        | item2    | Waypoint((472.6, 228.6)), | 342.0     | 343      |
        | exit     | Waypoint((485.0, 211.7)), | 17.3      | 15       |
        """
        self.map_init(plane=Luofu_ScalegorgeWaterscape, floor="F1", position=(567.4, 280.2))
        self.register_domain_exit(Waypoint((485.0, 211.7)), end_rotation=15)
        enemy1 = Waypoint((495.3, 273.7))
        node2 = Waypoint((482.8, 252.6))
        enemy2 = Waypoint((485.0, 211.7))
        item2 = Waypoint((472.6, 228.6))
        # ===== End of generated waypoints =====

        self.minimap.lock_rotation(270)
        self.clear_enemy(enemy1)
        self.rotation_set(0)
        self.minimap.lock_rotation(0)
        self.clear_item(
            node2,
            item2,
        )
        self.clear_enemy(
            enemy2,
        )

    def Luofu_ScalegorgeWaterscape_F1_X617Y99(self):
        """
        | Waypoint | Position                 | Direction | Rotation |
        | -------- | ------------------------ | --------- | -------- |
        | spawn    | Waypoint((617.3, 99.4)), | 6.7       | 1        |
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

        self.minimap.lock_rotation(90)
        # Ignore item, too close to enemy
        self.clear_enemy(enemy_X701Y242)

    def Luofu_ScalegorgeWaterscape_F1_X791Y245(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((791.2, 245.8)), | 22.7      | 18       |
        | item     | Waypoint((792.4, 224.5)), | 355.8     | 350      |
        | enemy    | Waypoint((802.3, 198.7)), | 22.7      | 20       |
        | exit     | Waypoint((801.6, 199.4)), | 210.2     | 13       |
        """
        self.map_init(plane=Luofu_ScalegorgeWaterscape, floor="F1", position=(791.2, 245.8))
        self.register_domain_exit(Waypoint((801.6, 199.4)), end_rotation=13)
        item = Waypoint((792.4, 224.5))
        enemy = Waypoint((802.3, 198.7))
        # ===== End of generated waypoints =====

        self.minimap.lock_rotation(18)
        self.clear_item(item)
        self.clear_enemy(enemy)

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
