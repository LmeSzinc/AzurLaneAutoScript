from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_Cloudford
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_Cloudford_F1_X241Y947(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((240.4, 947.6)), | 274.2     | 274      |
        | node     | Waypoint((218.8, 948.8)), | 282.9     | 278      |
        | item     | Waypoint((222.4, 934.6)), | 311.8     | 306      |
        | enemy    | Waypoint((197.2, 947.4)), | 282.6     | 260      |
        | exit     | Waypoint((193.1, 947.2)), | 12.8      | 274      |
        """
        self.map_init(plane=Luofu_Cloudford, floor="F1", position=(240.4, 947.6))
        self.register_domain_exit(Waypoint((193.1, 947.2)), end_rotation=274)
        node = Waypoint((218.8, 948.8))
        item = Waypoint((222.4, 934.6))
        enemy = Waypoint((197.2, 947.4))
        # ===== End of generated waypoints =====

        # ignore item
        # self.clear_item(item)
        self.clear_enemy(
            enemy,
        )

    def Luofu_Cloudford_F1_X257Y947(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((257.3, 951.2)), | 274.2     | 274      |
        | item     | Waypoint((236.8, 934.2)), | 302.7     | 299      |
        | node     | Waypoint((221.6, 946.2)), | 272.8     | 269      |
        | enemy    | Waypoint((193.7, 949.5)), | 143.8     | 269      |
        | exit     | Waypoint((194.4, 947.2)), | 4.2       | 274      |
        """
        self.map_init(plane=Luofu_Cloudford, floor="F1", position=(257.3, 947))
        self.register_domain_exit(Waypoint((194.4, 947.2)), end_rotation=274)
        item = Waypoint((236.8, 934.2))
        node = Waypoint((221.6, 946.2))
        enemy = Waypoint((193.7, 949.5))
        # ===== End of generated waypoints =====

        """
        Notes
        Luofu_Cloudford_F1_X257Y947 is the same as Luofu_Cloudford_F1_X257Y951
        but for wrong spawn point detected
        """

        self.clear_item(item)
        self.clear_enemy(
            node,
            enemy
        )

    def Luofu_Cloudford_F1_X257Y951(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((257.3, 951.2)), | 274.2     | 274      |
        | item     | Waypoint((236.8, 934.2)), | 302.7     | 299      |
        | node     | Waypoint((221.6, 946.2)), | 272.8     | 269      |
        | enemy    | Waypoint((193.7, 949.5)), | 143.8     | 269      |
        | exit     | Waypoint((194.4, 947.2)), | 4.2       | 274      |
        """
        self.map_init(plane=Luofu_Cloudford, floor="F1", position=(257.3, 951.2))
        self.register_domain_exit(Waypoint((194.4, 947.2)), end_rotation=274)
        item = Waypoint((236.8, 934.2))
        node = Waypoint((221.6, 946.2))
        enemy = Waypoint((193.7, 949.5))
        # ===== End of generated waypoints =====

        self.clear_item(item)
        self.clear_enemy(
            node,
            enemy
        )

    def Luofu_Cloudford_F1_X283Y865(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((283.4, 865.3)), | 6.7       | 4        |
        | item     | Waypoint((297.0, 841.4)), | 36.1      | 31       |
        | enemy    | Waypoint((282.4, 814.2)), | 8.1       | 1        |
        | exit     | Waypoint((284.5, 816.8)), | 5.7       | 1        |
        """
        self.map_init(plane=Luofu_Cloudford, floor="F1", position=(283.4, 865.3))
        self.register_domain_exit(Waypoint((284.5, 816.8)), end_rotation=1)
        item = Waypoint((297.0, 841.4))
        enemy = Waypoint((282.4, 814.2))
        # ===== End of generated waypoints =====

        self.clear_item(item)
        self.clear_enemy(enemy)

    def Luofu_Cloudford_F1_X431Y593(self):
        """
        | Waypoint        | Position                  | Direction | Rotation |
        | --------------- | ------------------------- | --------- | -------- |
        | spawn           | Waypoint((431.5, 593.4)), | 2.7       | 357      |
        | item1           | Waypoint((373.8, 592.8)), | 263.8     | 267      |
        | enemy1_X341Y586 | Waypoint((341.2, 586.8)), | 274.2     | 274      |
        | item2           | Waypoint((310.4, 582.2)), | 289.0     | 288      |
        | enemy2          | Waypoint((275.9, 584.9)), | 274.1     | 271      |
        | exit            | Waypoint((275.9, 584.9)), | 274.1     | 271      |
        """
        self.map_init(plane=Luofu_Cloudford, floor="F1", position=(431.5, 593.4))
        self.register_domain_exit(Waypoint((275.9, 584.9)), end_rotation=271)
        item1 = Waypoint((373.8, 592.8))
        enemy1_X341Y586 = Waypoint((341.2, 586.8))
        item2 = Waypoint((310.4, 582.2))
        enemy2 = Waypoint((275.9, 584.9))
        # ===== End of generated waypoints =====

        # 1
        self.clear_item(
            item1.straight_run(),
        )
        self.clear_enemy(
            enemy1_X341Y586.straight_run(),
        )
        # 2
        self.clear_item(item2)
        self.clear_enemy(enemy2)
