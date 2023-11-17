from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_ArtisanshipCommission
from tasks.map.route.base import locked_position
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_ArtisanshipCommission_F1_X41Y640(self):
        """
        | Waypoint | Position                 | Direction | Rotation |
        | -------- | ------------------------ | --------- | -------- |
        | spawn    | Waypoint((41.4, 639.9)), | 4.5       | 4        |
        | enemy1   | Waypoint((40.2, 576.2)), | 4.3       | 4        |
        | enemy2   | Waypoint((34.3, 494.4)), | 192.7     | 1        |
        | exit_    | Waypoint((34.3, 494.4)), | 192.7     | 1        |
        | exit1    | Waypoint((22.3, 486.2)), | 8.2       | 1        |
        | exit2    | Waypoint((41.2, 485.2)), | 4.3       | 1        |
        """
        self.map_init(plane=Luofu_ArtisanshipCommission, floor="F1", position=(41.4, 639.9))
        self.register_domain_exit(
            Waypoint((34.3, 494.4)), end_rotation=1,
            left_door=Waypoint((22.3, 486.2)), right_door=Waypoint((41.2, 485.2)))
        enemy1 = Waypoint((40.2, 576.2))
        enemy2 = Waypoint((34.3, 494.4))
        # ===== End of generated waypoints =====

        self.minimap.lock_rotation(0)
        self.clear_enemy(enemy1)
        self.clear_enemy(enemy2)

    @locked_position
    def Luofu_ArtisanshipCommission_F1_X185Y361(self):
        """
        | Waypoint       | Position                  | Direction | Rotation |
        | -------------- | ------------------------- | --------- | -------- |
        | spawn          | Waypoint((185.4, 361.4)), | 157.2     | 151      |
        | enemy_X212Y398 | Waypoint((212.5, 398.4)), | 149.9     | 327      |
        | item           | Waypoint((232.4, 388.4)), | 129.9     | 133      |
        | exit_          | Waypoint((217.4, 405.1)), | 166.7     | 168      |
        | exit1          | Waypoint((226.2, 411.6)), | 171.7     | 163      |
        | exit2          | Waypoint((209.0, 419.4)), | 157.4     | 156      |
        """
        self.map_init(plane=Luofu_ArtisanshipCommission, floor="F1", position=(185.4, 361.4))
        self.register_domain_exit(
            Waypoint((217.4, 405.1)), end_rotation=168,
            left_door=Waypoint((226.2, 411.6)), right_door=Waypoint((209.0, 419.4)))
        enemy_X212Y398 = Waypoint((212.5, 398.4))
        item = Waypoint((232.4, 388.4))
        # ===== End of generated waypoints =====

        # Enemy first, then go back for item
        self.clear_enemy(enemy_X212Y398)
        self.clear_item(item)

    def Luofu_ArtisanshipCommission_F1_X217Y807(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((217.3, 807.4)), | 190.1     | 184      |
        | item     | Waypoint((221.2, 833.4)), | 166.7     | 163      |
        | enemy    | Waypoint((216.2, 860.2)), | 193.1     | 188      |
        | exit_    | Waypoint((215.7, 861.4)), | 11.3      | 186      |
        | exit1    | Waypoint((224.2, 870.2)), | 179.9     | 179      |
        | exit2    | Waypoint((208.4, 870.3)), | 206.0     | 200      |
        """
        self.map_init(plane=Luofu_ArtisanshipCommission, floor="F1", position=(217.3, 807.4))
        self.register_domain_exit(
            Waypoint((215.7, 861.4)), end_rotation=186,
            left_door=Waypoint((224.2, 870.2)), right_door=Waypoint((208.4, 870.3)))
        item = Waypoint((221.2, 833.4))
        enemy = Waypoint((216.2, 860.2))
        # ===== End of generated waypoints =====

        # self.clear_item(item)
        self.clear_enemy(enemy)

    def Luofu_ArtisanshipCommission_F1_X473Y920(self):
        """
        | Waypoint    | Position                  | Direction | Rotation |
        | ----------- | ------------------------- | --------- | -------- |
        | spawn       | Waypoint((473.5, 920.9)), | 4.5       | 4        |
        | enemy1left  | Waypoint((475.0, 848.4)), | 4.4       | 4        |
        | enemy2right | Waypoint((493.5, 807.4)), | 157.1     | 48       |
        | enemy3      | Waypoint((528.9, 782.9)), | 198.5     | 91       |
        | exit_       | Waypoint((528.9, 782.9)), | 198.5     | 91       |
        | exit1       | Waypoint((537.0, 773.2)), | 99.0      | 89       |
        | exit2       | Waypoint((537.5, 790.6)), | 101.1     | 91       |
        """
        self.map_init(plane=Luofu_ArtisanshipCommission, floor="F1", position=(473.5, 920.9))
        self.register_domain_exit(
            Waypoint((528.9, 782.9)), end_rotation=91,
            left_door=Waypoint((537.0, 773.2)), right_door=Waypoint((537.5, 790.6)))
        enemy1left = Waypoint((475.0, 848.4))
        enemy2right = Waypoint((493.5, 807.4))
        enemy3 = Waypoint((528.9, 782.9))
        # ===== End of generated waypoints =====

        self.rotation_set(30)
        self.clear_enemy(
            enemy1left,
            enemy2right,
        )
        self.clear_enemy(enemy3)
        if self.minimap.position_diff(enemy3.position) > 25:
            self.clear_enemy(enemy3)

    def Luofu_ArtisanshipCommission_F1_X543Y269(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((543.3, 269.6)), | 94.2      | 91       |
        | enemy1   | Waypoint((619.2, 268.0)), | 45.8      | 91       |
        | enemy2   | Waypoint((654.6, 266.6)), | 282.7     | 87       |
        | exit_    | Waypoint((654.6, 266.6)), | 282.7     | 87       |
        | exit1    | Waypoint((664.6, 258.5)), | 96.8      | 87       |
        | exit2    | Waypoint((665.0, 274.4)), | 96.8      | 87       |
        """
        self.map_init(plane=Luofu_ArtisanshipCommission, floor="F1", position=(543.3, 269.6))
        self.register_domain_exit(
            Waypoint((654.6, 266.6)), end_rotation=87,
            left_door=Waypoint((664.6, 258.5)), right_door=Waypoint((665.0, 274.4)))
        enemy1 = Waypoint((619.2, 268.0))
        enemy2 = Waypoint((654.6, 266.6))
        # ===== End of generated waypoints =====

        self.clear_enemy(enemy1)
        self.clear_enemy(enemy2)

    def Luofu_ArtisanshipCommission_F1_X655Y537(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((655.5, 537.3)), | 6.7       | 1        |
        | item     | Waypoint((680.6, 503.2)), | 30.1      | 27       |
        | enemy    | Waypoint((656.2, 484.2)), | 11.1      | 184      |
        | exit_    | Waypoint((647.0, 477.5)), | 357.8     | 352      |
        """
        self.map_init(plane=Luofu_ArtisanshipCommission, floor="F1", position=(655.5, 537.3))
        self.register_domain_exit(Waypoint((647.0, 477.5)), end_rotation=352)
        item = Waypoint((680.6, 503.2))
        enemy = Waypoint((656.2, 484.2))
        # ===== End of generated waypoints =====

        # Ignore item, bad way
        self.clear_enemy(enemy)

    def Luofu_ArtisanshipCommission_F1_X667Y189(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((667.0, 189.2)), | 282.2     | 274      |
        | enemy1   | Waypoint((596.8, 189.1)), | 282.5     | 278      |
        | node1    | Waypoint((587.3, 187.8)), | 282.6     | 276      |
        | node2    | Waypoint((566.8, 190.1)), | 282.6     | 276      |
        | enemy2   | Waypoint((532.2, 204.2)), | 94.2      | 274      |
        | exit_    | Waypoint((532.2, 204.2)), | 94.2      | 274      |
        | exit1    | Waypoint((521.0, 213.2)), | 275.9     | 274      |
        | exit2    | Waypoint((521.5, 195.5)), | 275.8     | 274      |
        """
        self.map_init(plane=Luofu_ArtisanshipCommission, floor="F1", position=(667.0, 189.2))
        self.register_domain_exit(
            Waypoint((532.2, 204.2)), end_rotation=274,
            left_door=Waypoint((521.0, 213.2)), right_door=Waypoint((521.5, 195.5)))
        enemy1 = Waypoint((596.8, 189.1))
        node1 = Waypoint((587.3, 187.8))
        node2 = Waypoint((566.8, 190.1))
        enemy2 = Waypoint((532.2, 204.2))
        # ===== End of generated waypoints =====

        self.clear_enemy(enemy1)
        self.clear_enemy(
            node1.set_threshold(5),
            node2.set_threshold(5),
            enemy2
        )
