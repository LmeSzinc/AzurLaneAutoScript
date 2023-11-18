from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_SilvermaneGuardRestrictedZone
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_SilvermaneGuardRestrictedZone_F1_X191Y199(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((191.4, 199.4)), | 94.2      | 91       |
        | enemy1   | Waypoint((241.0, 198.6)), | 102.7     | 94       |
        | item2    | Waypoint((272.5, 192.5)), | 86.2      | 82       |
        | node2    | Waypoint((284.8, 204.4)), | 343.8     | 108      |
        | node3    | Waypoint((308.2, 208.8)), | 101.2     | 98       |
        | item3    | Waypoint((326.4, 196.4)), | 45.8      | 45       |
        | enemy3   | Waypoint((352.2, 198.4)), | 99.2      | 91       |
        | exit_    | Waypoint((352.2, 198.4)), | 99.2      | 91       |
        | exit1    | Waypoint((356.6, 192.2)), | 350.5     | 78       |
        | exit2    | Waypoint((358.0, 206.2)), | 101.2     | 101      |
        """
        self.map_init(plane=Jarilo_SilvermaneGuardRestrictedZone, floor="F1", position=(191.4, 199.4))
        self.register_domain_exit(
            Waypoint((352.2, 198.4)), end_rotation=91,
            left_door=Waypoint((356.6, 192.2)), right_door=Waypoint((358.0, 206.2)))
        enemy1 = Waypoint((241.0, 198.6))
        item2 = Waypoint((272.5, 192.5))
        node2 = Waypoint((284.8, 204.4))
        node3 = Waypoint((308.2, 208.8))
        item3 = Waypoint((326.4, 196.4))
        enemy3 = Waypoint((352.2, 198.4))
        # ===== End of generated waypoints =====

        self.minimap.lock_rotation(90)
        self.clear_enemy(enemy1)
        self.clear_item(item2)
        # Go through trench gaps, a moving enemy in it
        self.goto(
            node2.set_threshold(3),
            node3.set_threshold(3),
        )
        self.clear_enemy(enemy3)

    def Jarilo_SilvermaneGuardRestrictedZone_F1_X221Y426(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((221.3, 426.1)), | 274.2     | 274      |
        | item     | Waypoint((195.9, 434.9)), | 237.2     | 234      |
        | enemy    | Waypoint((172.9, 425.9)), | 274.2     | 274      |
        | exit_    | Waypoint((172.9, 425.9)), | 274.2     | 274      |
        | exit1    | Waypoint((164.0, 435.4)), | 281.9     | 274      |
        | exit2    | Waypoint((163.9, 417.7)), | 281.9     | 274      |
        """
        self.map_init(plane=Jarilo_SilvermaneGuardRestrictedZone, floor="F1", position=(221.3, 426.1))
        self.register_domain_exit(
            Waypoint((172.9, 425.9)), end_rotation=274,
            left_door=Waypoint((164.0, 435.4)), right_door=Waypoint((163.9, 417.7)))
        item = Waypoint((195.9, 434.9))
        enemy = Waypoint((172.9, 425.9))
        # ===== End of generated waypoints =====

        self.clear_item(item)
        self.clear_enemy(enemy)

    def Jarilo_SilvermaneGuardRestrictedZone_F1_X227Y425(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((227.7, 425.5)), | 274.2     | 274      |
        | item     | Waypoint((208.3, 414.8)), | 303.8     | 301      |
        | enemy    | Waypoint((170.2, 426.2)), | 274.2     | 274      |
        | exit_    | Waypoint((170.2, 426.2)), | 274.2     | 274      |
        | exit1    | Waypoint((158.5, 432.5)), | 282.0     | 274      |
        | exit2    | Waypoint((158.8, 418.6)), | 282.0     | 274      |
        """
        self.map_init(plane=Jarilo_SilvermaneGuardRestrictedZone, floor="F1", position=(227.7, 425.5))
        self.register_domain_exit(
            Waypoint((170.2, 426.2)), end_rotation=274,
            left_door=Waypoint((158.5, 432.5)), right_door=Waypoint((158.8, 418.6)))
        item = Waypoint((208.3, 414.8))
        enemy = Waypoint((170.2, 426.2))
        # ===== End of generated waypoints =====

        # Ignore item
        self.clear_enemy(enemy)

    def Jarilo_SilvermaneGuardRestrictedZone_F1_X317Y425(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((317.4, 425.4)), | 274.2     | 274      |
        | item1    | Waypoint((282.4, 434.2)), | 263.8     | 260      |
        | enemy1   | Waypoint((252.6, 426.6)), | 283.0     | 276      |
        | enemy2   | Waypoint((166.1, 424.5)), | 182.6     | 267      |
        | exit_    | Waypoint((165.1, 425.2)), | 6.4       | 274      |
        | exit1    | Waypoint((157.7, 432.7)), | 275.8     | 274      |
        | exit2    | Waypoint((157.6, 419.0)), | 282.0     | 274      |
        """
        self.map_init(plane=Jarilo_SilvermaneGuardRestrictedZone, floor="F1", position=(317.4, 425.4))
        self.register_domain_exit(
            Waypoint((165.1, 425.2)), end_rotation=274,
            left_door=Waypoint((157.7, 432.7)), right_door=Waypoint((157.6, 419.0)))
        item1 = Waypoint((282.4, 434.2))
        enemy1 = Waypoint((252.6, 426.6))
        enemy2 = Waypoint((166.1, 424.5))
        # ===== End of generated waypoints =====

        self.clear_item(item1)
        self.clear_enemy(enemy1)
        self.clear_enemy(
            enemy1.set_threshold(5),
            enemy2,
        )

    def Jarilo_SilvermaneGuardRestrictedZone_F1_X371Y419(self):
        """
        | Waypoint    | Position                  | Direction | Rotation |
        | ----------- | ------------------------- | --------- | -------- |
        | spawn       | Waypoint((371.6, 419.4)), | 274.2     | 271      |
        | enemy1right | Waypoint((320.5, 424.5)), | 274.2     | 274      |
        | enemy1left  | Waypoint((304.5, 424.6)), | 274.3     | 274      |
        | item2       | Waypoint((282.8, 434.6)), | 274.3     | 276      |
        | enemy2      | Waypoint((249.3, 424.4)), | 274.2     | 271      |
        | enemy3      | Waypoint((168.0, 424.4)), | 279.8     | 274      |
        | exit_       | Waypoint((164.2, 426.2)), | 274.3     | 274      |
        """
        self.map_init(plane=Jarilo_SilvermaneGuardRestrictedZone, floor="F1", position=(371.6, 419.4))
        self.register_domain_exit(Waypoint((164.2, 426.2)), end_rotation=274)
        enemy1right = Waypoint((320.5, 424.5))
        enemy1left = Waypoint((304.5, 424.6))
        item2 = Waypoint((282.8, 434.6))
        enemy2 = Waypoint((249.3, 424.4))
        enemy3 = Waypoint((168.0, 424.4))
        # ===== End of generated waypoints =====

        self.clear_enemy(
            enemy1right,
            enemy1left,
        )
        self.clear_item(item2)
        self.clear_enemy(enemy2)
        self.clear_enemy(
            enemy2.set_threshold(5),
            enemy3
        )

    def Jarilo_SilvermaneGuardRestrictedZone_F1_X371Y425(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((371.6, 425.3)), | 274.2     | 274      |
        | item1    | Waypoint((350.3, 410.5)), | 318.0     | 315      |
        | enemy1   | Waypoint((304.0, 424.2)), | 274.2     | 276      |
        | enemy2   | Waypoint((247.9, 426.4)), | 11.2      | 45       |
        | enemy3   | Waypoint((163.9, 426.5)), | 282.9     | 278      |
        | exit_    | Waypoint((163.9, 426.5)), | 282.9     | 278      |
        | exit1    | Waypoint((157.9, 433.4)), | 275.9     | 274      |
        | exit2    | Waypoint((158.0, 419.2)), | 281.9     | 274      |
        """
        self.map_init(plane=Jarilo_SilvermaneGuardRestrictedZone, floor="F1", position=(371.6, 425.3))
        self.register_domain_exit(
            Waypoint((163.9, 426.5)), end_rotation=278,
            left_door=Waypoint((157.9, 433.4)), right_door=Waypoint((158.0, 419.2)))
        item1 = Waypoint((350.3, 410.5))
        enemy1 = Waypoint((304.0, 424.2))
        enemy2 = Waypoint((247.9, 426.4))
        enemy3 = Waypoint((163.9, 426.5))
        # ===== End of generated waypoints =====

        self.clear_item(item1)
        self.clear_enemy(enemy1)
        self.clear_enemy(enemy2)
        self.clear_enemy(enemy3)

    def Jarilo_SilvermaneGuardRestrictedZone_F1_X419Y180(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((419.4, 179.8)), | 166.8     | 163      |
        | enemy    | Waypoint((437.0, 227.2)), | 166.6     | 156      |
        | exit_    | Waypoint((437.0, 227.2)), | 166.6     | 156      |
        | exit1    | Waypoint((449.1, 228.5)), | 171.7     | 163      |
        | exit2    | Waypoint((431.7, 235.1)), | 171.7     | 163      |
        """
        self.map_init(plane=Jarilo_SilvermaneGuardRestrictedZone, floor="F1", position=(419.4, 179.8))
        self.register_domain_exit(
            Waypoint((437.0, 227.2)), end_rotation=156,
            left_door=Waypoint((449.1, 228.5)), right_door=Waypoint((431.7, 235.1)))
        enemy = Waypoint((437.0, 227.2))
        # ===== End of generated waypoints =====

        self.clear_enemy(enemy)

    def Jarilo_SilvermaneGuardRestrictedZone_F1_X421Y173(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((421.5, 173.4)), | 172.8     | 165      |
        | item     | Waypoint((418.5, 218.3)), | 183.8     | 181      |
        | enemy    | Waypoint((440.2, 232.4)), | 166.6     | 154      |
        | exit_    | Waypoint((440.2, 232.4)), | 166.6     | 154      |
        | exit1    | Waypoint((449.4, 237.1)), | 157.5     | 154      |
        | exit2    | Waypoint((439.2, 240.8)), | 157.3     | 156      |
        """
        self.map_init(plane=Jarilo_SilvermaneGuardRestrictedZone, floor="F1", position=(421.5, 173.4))
        self.register_domain_exit(
            Waypoint((440.2, 232.4)), end_rotation=154,
            left_door=Waypoint((449.4, 237.1)), right_door=Waypoint((439.2, 240.8)))
        item = Waypoint((418.5, 218.3))
        enemy = Waypoint((440.2, 232.4))
        # ===== End of generated waypoints =====

        self.clear_item(item)
        self.clear_enemy(enemy)

    def Jarilo_SilvermaneGuardRestrictedZone_F1_X569Y495(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((569.1, 495.0)), | 190.1     | 184      |
        | item1    | Waypoint((562.4, 528.4)), | 203.1     | 200      |
        | enemy1   | Waypoint((566.2, 572.0)), | 282.8     | 181      |
        | item2    | Waypoint((574.0, 583.2)), | 139.4     | 140      |
        | enemy3   | Waypoint((542.6, 613.0)), | 239.8     | 237      |
        | node4    | Waypoint((527.6, 625.4)), | 21.0      | 283      |
        | item3    | Waypoint((536.4, 628.1)), | 210.2     | 204      |
        | enemy4   | Waypoint((494.2, 611.8)), | 274.2     | 274      |
        | exit_    | Waypoint((494.2, 611.8)), | 274.2     | 274      |
        | exit1    | Waypoint((489.2, 617.2)), | 282.6     | 276      |
        | exit2    | Waypoint((489.8, 606.2)), | 282.1     | 276      |
        """
        self.map_init(plane=Jarilo_SilvermaneGuardRestrictedZone, floor="F1", position=(569.1, 495.0))
        self.register_domain_exit(
            Waypoint((494.2, 611.8)), end_rotation=274,
            left_door=Waypoint((489.2, 617.2)), right_door=Waypoint((489.8, 606.2)))
        item1 = Waypoint((562.4, 528.4))
        enemy1 = Waypoint((566.2, 572.0))
        item2 = Waypoint((574.0, 583.2))
        enemy3 = Waypoint((542.6, 613.0))
        node4 = Waypoint((527.6, 625.4))
        item3 = Waypoint((536.4, 628.1))
        enemy4 = Waypoint((494.2, 611.8))
        # ===== End of generated waypoints =====

        # 1
        self.clear_item(item1)
        self.clear_enemy(enemy1)
        self.clear_item(item2)
        # 3
        self.clear_enemy(
            enemy3.straight_run(),
        )
        self.clear_item(
            item3,
        )
        # 4
        self.clear_enemy(
            node4.set_threshold(3),
            enemy4.straight_run(),
        )
