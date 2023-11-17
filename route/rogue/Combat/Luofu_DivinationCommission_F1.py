from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_DivinationCommission
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_DivinationCommission_F1_X63Y303(self):
        """
        | Waypoint | Position                 | Direction | Rotation |
        | -------- | ------------------------ | --------- | -------- |
        | spawn    | Waypoint((63.7, 303.4)), | 4.5       | 4        |
        | item     | Waypoint((53.1, 268.1)), | 356.3     | 354      |
        | enemy1   | Waypoint((65.3, 245.4)), | 157.1     | 24       |
        | enemy2   | Waypoint((64.4, 220.2)), | 6.8       | 1        |
        | exit_    | Waypoint((64.4, 220.2)), | 6.8       | 1        |
        | exit1    | Waypoint((55.2, 212.8)), | 4.1       | 1        |
        | exit2    | Waypoint((73.2, 213.3)), | 6.9       | 1        |
        """
        self.map_init(plane=Luofu_DivinationCommission, floor="F1", position=(63.7, 303.4))
        self.register_domain_exit(
            Waypoint((64.4, 220.2)), end_rotation=1,
            left_door=Waypoint((55.2, 212.8)), right_door=Waypoint((73.2, 213.3)))
        item = Waypoint((53.1, 268.1))
        enemy1 = Waypoint((65.3, 245.4))
        enemy2 = Waypoint((64.4, 220.2))
        # ===== End of generated waypoints =====

        self.minimap.lock_rotation(0)
        self.clear_item(item)
        self.clear_enemy(
            item.set_threshold(7),
            enemy1,
        )
        self.clear_enemy(
            enemy1.set_threshold(5),
            enemy2,
        )

    def Luofu_DivinationCommission_F1_X97Y457(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((97.2, 456.9)),  | 192.6     | 184      |
        | enemy1   | Waypoint((104.6, 502.8)), | 185.7     | 168      |
        | enemy2   | Waypoint((126.6, 528.0)), | 48.1      | 140      |
        | exit_    | Waypoint((126.6, 528.0)), | 48.1      | 140      |
        | exit1    | Waypoint((137.5, 527.4)), | 137.7     | 140      |
        | exit2    | Waypoint((125.1, 540.0)), | 135.9     | 140      |
        """
        self.map_init(plane=Luofu_DivinationCommission, floor="F1", position=(97.2, 456.9))
        self.register_domain_exit(
            Waypoint((126.6, 528.0)), end_rotation=140,
            left_door=Waypoint((137.5, 527.4)), right_door=Waypoint((125.1, 540.0)))
        enemy1 = Waypoint((104.6, 502.8))
        enemy2 = Waypoint((126.6, 528.0))
        # ===== End of generated waypoints =====

        self.clear_enemy(enemy1)
        self.clear_enemy(
            enemy2.straight_run(),
        )

    def Luofu_DivinationCommission_F1_X737Y237(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((737.2, 237.6)), | 192.6     | 184      |
        | enemy1   | Waypoint((740.8, 318.8)), | 192.6     | 184      |
        | enemy2   | Waypoint((737.8, 360.9)), | 179.8     | 181      |
        | exit_    | Waypoint((737.8, 360.9)), | 179.8     | 181      |
        | exit1    | Waypoint((747.6, 367.2)), | 180.1     | 181      |
        | exit2    | Waypoint((729.6, 367.5)), | 191.8     | 181      |
        """
        self.map_init(plane=Luofu_DivinationCommission, floor="F1", position=(737.2, 237.6))
        self.register_domain_exit(
            Waypoint((737.8, 360.9)), end_rotation=181,
            left_door=Waypoint((747.6, 367.2)), right_door=Waypoint((729.6, 367.5)))
        enemy1 = Waypoint((740.8, 318.8))
        enemy2 = Waypoint((737.8, 360.9))
        # ===== End of generated waypoints =====

        self.minimap.lock_rotation(180)
        self.clear_enemy(enemy1)
        # Possible enemy2
        self.clear_enemy(
            enemy1.set_threshold(5),
            enemy2,
        )
        # Enemy3
        if self.minimap.position_diff(enemy2.position) > 35:
            self.clear_enemy(
                enemy1.set_threshold(5),
                enemy2,
            )

    def Luofu_DivinationCommission_F1_X737Y372(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((737.4, 372.2)), | 4.5       | 4        |
        | enemy1   | Waypoint((738.3, 288.3)), | 4.4       | 4        |
        | enemy2   | Waypoint((737.3, 245.6)), | 96.8      | 1        |
        | exit_    | Waypoint((737.3, 245.6)), | 96.8      | 1        |
        | exit1    | Waypoint((730.1, 236.6)), | 4.1       | 1        |
        | exit2    | Waypoint((748.0, 237.0)), | 5.6       | 1        |
        """
        self.map_init(plane=Luofu_DivinationCommission, floor="F1", position=(737.4, 372.2))
        self.register_domain_exit(
            Waypoint((737.3, 245.6)), end_rotation=1,
            left_door=Waypoint((730.1, 236.6)), right_door=Waypoint((748.0, 237.0)))
        enemy1 = Waypoint((738.3, 288.3))
        enemy2 = Waypoint((737.3, 245.6))
        # ===== End of generated waypoints =====

        self.clear_enemy(enemy1)
        self.clear_enemy(enemy2)
