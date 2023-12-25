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
        | node3       | Waypoint((358.4, 280.5)), | 282.9     | 278      |
        | enemy3      | Waypoint((340.2, 281.8)), | 275.8     | 87       |
        | node4       | Waypoint((325.3, 280.5)), | 275.9     | 274      |
        | enemy4      | Waypoint((283.6, 280.0)), | 282.7     | 276      |
        | exit_       | Waypoint((278.4, 280.2)), | 274.2     | 271      |
        | exit1       | Waypoint((274.2, 286.0)), | 275.8     | 271      |
        | exit2       | Waypoint((274.2, 275.8)), | 275.8     | 271      |
        """
        self.map_init(plane=Luofu_ScalegorgeWaterscape, floor="F1", position=(415.4, 261.6))
        self.register_domain_exit(
            Waypoint((278.4, 280.2)), end_rotation=271,
            left_door=Waypoint((274.2, 286.0)), right_door=Waypoint((274.2, 275.8)))
        item1 = Waypoint((396.6, 270.2))
        enemy1right = Waypoint((385.0, 274.4))
        node2 = Waypoint((381.0, 281.0))
        enemy1left = Waypoint((384.2, 292.0))
        node3 = Waypoint((358.4, 280.5))
        enemy3 = Waypoint((340.2, 281.8))
        node4 = Waypoint((325.3, 280.5))
        enemy4 = Waypoint((283.6, 280.0))
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
            node3.set_threshold(3),
            enemy3,
        )
        self.clear_enemy(
            node4.set_threshold(3),
            enemy4,
        )

    def Luofu_ScalegorgeWaterscape_F1_X467Y405(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((467.5, 405.5)), | 274.2     | 274      |
        | item     | Waypoint((444.6, 390.5)), | 20.4      | 18       |
        | node     | Waypoint((439.0, 388.5)), | 355.9     | 352      |
        | enemy1   | Waypoint((434.0, 406.2)), | 274.2     | 274      |
        | enemy2   | Waypoint((432.2, 367.2)), | 355.9     | 352      |
        | exit_    | Waypoint((431.2, 363.2)), | 6.6       | 1        |
        | exit1    | Waypoint((426.9, 357.1)), | 4.5       | 4        |
        | exit2    | Waypoint((438.2, 358.0)), | 4.4       | 4        |
        """
        self.map_init(plane=Luofu_ScalegorgeWaterscape, floor="F1", position=(467.5, 405.5))
        self.register_domain_exit(
            Waypoint((431.2, 363.2)), end_rotation=1,
            left_door=Waypoint((426.9, 357.1)), right_door=Waypoint((438.2, 358.0)))
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
        | node2    | Waypoint((491.3, 269.4)), | 339.1     | 334      |
        | enemy2   | Waypoint((485.0, 211.7)), | 17.3      | 15       |
        | item2    | Waypoint((472.6, 228.6)), | 342.0     | 343      |
        | exit_    | Waypoint((485.0, 211.7)), | 17.3      | 15       |
        | exit1    | Waypoint((481.4, 207.3)), | 127.7     | 27       |
        | exit2    | Waypoint((491.0, 209.4)), | 30.1      | 27       |
        """
        self.map_init(plane=Luofu_ScalegorgeWaterscape, floor="F1", position=(567.4, 280.2))
        self.register_domain_exit(
            Waypoint((485.0, 211.7)), end_rotation=15,
            left_door=Waypoint((481.4, 207.3)), right_door=Waypoint((491.0, 209.4)))
        enemy1 = Waypoint((495.3, 273.7))
        node2 = Waypoint((491.3, 269.4))
        enemy2 = Waypoint((485.0, 211.7))
        item2 = Waypoint((472.6, 228.6))
        # ===== End of generated waypoints =====

        self.minimap.lock_rotation(270)
        self.clear_enemy(enemy1)
        self.rotation_set(0)
        self.minimap.lock_rotation(0)
        self.clear_item(
            node2.set_threshold(5),
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
        | exit_    | Waypoint((617.2, 64.6)), | 12.6      | 4        |
        | exit1    | Waypoint((609.2, 57.2)), | 6.9       | 4        |
        | exit2    | Waypoint((623.4, 56.6)), | 11.1      | 4        |
        """
        self.map_init(plane=Luofu_ScalegorgeWaterscape, floor="F1", position=(617.3, 99.4))
        self.register_domain_exit(
            Waypoint((617.2, 64.6)), end_rotation=4,
            left_door=Waypoint((609.2, 57.2)), right_door=Waypoint((623.4, 56.6)))
        item = Waypoint((610.5, 88.6))
        enemy = Waypoint((616.2, 64.4))
        # ===== End of generated waypoints =====

        self.clear_item(item)
        self.clear_enemy(enemy)

    def Luofu_ScalegorgeWaterscape_F1_X668Y243(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((668.9, 243.4)), | 96.7      | 91       |
        | item     | Waypoint((690.8, 236.8)), | 45.8      | 43       |
        | enemy    | Waypoint((701.6, 242.2)), | 98.0      | 89       |
        | exit_    | Waypoint((701.6, 242.2)), | 98.0      | 89       |
        | exit1    | Waypoint((710.0, 238.2)), | 86.2      | 82       |
        | exit2    | Waypoint((710.0, 246.8)), | 102.9     | 103      |
        """
        self.map_init(plane=Luofu_ScalegorgeWaterscape, floor="F1", position=(668.9, 243.4))
        self.register_domain_exit(
            Waypoint((701.6, 242.2)), end_rotation=89,
            left_door=Waypoint((710.0, 238.2)), right_door=Waypoint((710.0, 246.8)))
        item = Waypoint((690.8, 236.8))
        enemy = Waypoint((701.6, 242.2))
        # ===== End of generated waypoints =====

        self.minimap.lock_rotation(90)
        # Ignore item, too close to enemy
        self.clear_enemy(enemy)

    def Luofu_ScalegorgeWaterscape_F1_X791Y245(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((791.2, 245.8)), | 22.7      | 18       |
        | item     | Waypoint((792.4, 224.5)), | 355.8     | 350      |
        | enemy    | Waypoint((802.3, 198.7)), | 22.7      | 20       |
        | exit_    | Waypoint((801.6, 199.4)), | 210.2     | 13       |
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
        | exit_    | Waypoint((1090.7, 280.4)), | 282.8     | 274      |
        | exit1    | Waypoint((1085.4, 285.4)), | 284.7     | 278      |
        | exit2    | Waypoint((1085.6, 275.2)), | 282.2     | 274      |
        """
        self.map_init(plane=Luofu_ScalegorgeWaterscape, floor="F1", position=(1181.0, 279.5))
        self.register_domain_exit(
            Waypoint((1090.7, 280.4)), end_rotation=274,
            left_door=Waypoint((1085.4, 285.4)), right_door=Waypoint((1085.6, 275.2)))
        enemy1 = Waypoint((1160.6, 273.0))
        item1 = Waypoint((1161.2, 288.6))
        item3 = Waypoint((1125.2, 274.6))
        enemy2 = Waypoint((1128.4, 298.8))
        item2 = Waypoint((1125.0, 290.7))
        enemy4 = Waypoint((1091.8, 280.2))
        # ===== End of generated waypoints =====

        self.minimap.lock_rotation(270)
        # Ignore items and enemy2, as it's a straight way to exit
        self.clear_enemy(enemy1)
        self.clear_enemy(enemy4)
