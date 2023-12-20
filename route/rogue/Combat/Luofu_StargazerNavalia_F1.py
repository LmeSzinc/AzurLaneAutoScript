from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_StargazerNavalia
from tasks.map.route.base import locked_position
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_StargazerNavalia_F1_X183Y315(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((183.4, 315.6)), | 98.9      | 89       |
        | item     | Waypoint((208.5, 306.1)), | 82.5      | 80       |
        | enemy    | Waypoint((247.4, 320.2)), | 114.1     | 112      |
        | exit_    | Waypoint((243.4, 319.4)), | 274.2     | 89       |
        | exit1    | Waypoint((251.4, 311.5)), | 96.9      | 89       |
        | exit2    | Waypoint((251.4, 323.5)), | 96.9      | 89       |
        """
        self.map_init(plane=Luofu_StargazerNavalia, floor="F1", position=(183.4, 315.6))
        self.register_domain_exit(
            Waypoint((243.4, 319.4)), end_rotation=89,
            left_door=Waypoint((251.4, 311.5)), right_door=Waypoint((251.4, 323.5)))
        item = Waypoint((208.5, 306.1))
        enemy = Waypoint((247.4, 320.2))
        # ===== End of generated waypoints =====

        self.minimap.lock_rotation(90)
        self.clear_item(item)
        self.clear_enemy(enemy)

    @locked_position
    def Luofu_StargazerNavalia_F1_X203Y317(self):
        """
        | Waypoint       | Position                  | Direction | Rotation |
        | -------------- | ------------------------- | --------- | -------- |
        | spawn          | Waypoint((203.8, 317.4)), | 96.7      | 91       |
        | enemy          | Waypoint((254.2, 318.9)), | 96.8      | 91       |
        | exit_          | Waypoint((254.2, 318.9)), | 96.8      | 91       |
        | exit1_X258Y313 | Waypoint((258.1, 313.3)), | 94.2      | 91       |
        | exit2          | Waypoint((257.6, 325.5)), | 94.2      | 91       |
        """
        self.map_init(plane=Luofu_StargazerNavalia, floor="F1", position=(203.8, 317.4))
        self.register_domain_exit(
            Waypoint((254.2, 318.9)), end_rotation=91,
            left_door=Waypoint((258.1, 313.3)), right_door=Waypoint((257.6, 325.5)))
        enemy = Waypoint((254.2, 318.9))
        # ===== End of generated waypoints =====

        self.minimap.lock_rotation(90)
        self.clear_enemy(enemy)

    def Luofu_StargazerNavalia_F1_X215Y192(self):
        """
        | Waypoint    | Position                  | Direction | Rotation |
        | ----------- | ------------------------- | --------- | -------- |
        | spawn       | Waypoint((215.5, 192.6)), | 190.1     | 184      |
        | item1       | Waypoint((212.0, 241.6)), | 194.8     | 204      |
        | enemy1      | Waypoint((188.6, 248.2)), | 223.8     | 221      |
        | node2       | Waypoint((178.9, 278.9)), | 198.7     | 195      |
        | enemy4      | Waypoint((247.6, 317.2)), | 198.7     | 96       |
        | enemy2left  | Waypoint((216.6, 322.8)), | 101.1     | 96       |
        | enemy2right | Waypoint((176.6, 318.6)), | 206.2     | 103      |
        | exit_       | Waypoint((247.6, 317.2)), | 198.7     | 96       |
        | exit1       | Waypoint((252.6, 312.0)), | 96.9      | 89       |
        | exit2       | Waypoint((252.8, 324.8)), | 96.2      | 89       |
        """
        self.map_init(plane=Luofu_StargazerNavalia, floor="F1", position=(215.5, 192.6))
        self.register_domain_exit(
            Waypoint((247.6, 317.2)), end_rotation=96,
            left_door=Waypoint((252.6, 312.0)), right_door=Waypoint((252.8, 324.8)))
        item1 = Waypoint((212.0, 241.6))
        enemy1 = Waypoint((188.6, 248.2))
        node2 = Waypoint((178.9, 278.9))
        enemy4 = Waypoint((247.6, 317.2))
        enemy2left = Waypoint((216.6, 322.8))
        enemy2right = Waypoint((176.6, 318.6))
        # ===== End of generated waypoints =====

        # Ignore items
        self.clear_enemy(enemy1.straight_run())
        self.rotation_set(120)
        self.minimap.lock_rotation(120)
        self.clear_enemy(
            node2,
            enemy2right,
            enemy2left,
        )
        self.clear_enemy(
            enemy2left,
            enemy4,
        )

    def Luofu_StargazerNavalia_F1_X432Y593(self):
        """
        | Waypoint       | Position                  | Direction | Rotation |
        | -------------- | ------------------------- | --------- | -------- |
        | spawn          | Waypoint((432.7, 593.4)), | 96.7      | 91       |
        | event          | Waypoint((449.6, 606.4)), | 135.8     | 131      |
        | item1_X464Y586 | Waypoint((464.6, 586.5)), | 64.9      | 61       |
        | enemy1         | Waypoint((506.2, 596.2)), | 96.8      | 94       |
        | item2          | Waypoint((522.8, 589.0)), | 64.9      | 64       |
        | enemy3         | Waypoint((560.5, 601.8)), | 96.8      | 96       |
        | exit_          | Waypoint((565.6, 603.3)), | 94.2      | 91       |
        | exit1          | Waypoint((571.0, 597.0)), | 81.1      | 78       |
        | exit2          | Waypoint((570.8, 610.8)), | 96.8      | 96       |
        """
        self.map_init(plane=Luofu_StargazerNavalia, floor="F1", position=(432.7, 593.4))
        self.register_domain_exit(
            Waypoint((565.6, 603.3)), end_rotation=91,
            left_door=Waypoint((571.0, 597.0)), right_door=Waypoint((570.8, 610.8)))
        event = Waypoint((449.6, 606.4))
        item1_X464Y586 = Waypoint((464.6, 586.5))
        enemy1 = Waypoint((506.2, 596.2))
        item2 = Waypoint((522.8, 589.0))
        enemy3 = Waypoint((560.5, 601.8))
        # ===== End of generated waypoints =====

        self.minimap.lock_rotation(90)
        # Ignore items
        self.clear_enemy(enemy1)
        # Ignore enemy2
        self.clear_enemy(enemy3)
        if self.minimap.position_diff(enemy3.position) > 35:
            self.clear_enemy(enemy3)

    @locked_position
    def Luofu_StargazerNavalia_F1_X499Y581(self):
        """
        | Waypoint      | Position                  | Direction | Rotation |
        | ------------- | ------------------------- | --------- | -------- |
        | spawn         | Waypoint((499.6, 581.5)), | 157.2     | 151      |
        | item_X502Y605 | Waypoint((502.6, 605.0)), | 180.0     | 179      |
        | enemy         | Waypoint((519.0, 623.0)), | 149.8     | 149      |
        | exit_         | Waypoint((524.4, 624.7)), | 166.7     | 161      |
        | exit1         | Waypoint((533.4, 631.2)), | 160.8     | 158      |
        | exit2         | Waypoint((517.9, 636.5)), | 160.9     | 158      |
        """
        self.map_init(plane=Luofu_StargazerNavalia, floor="F1", position=(499.6, 581.5))
        self.register_domain_exit(
            Waypoint((524.4, 624.7)), end_rotation=161,
            left_door=Waypoint((533.4, 631.2)), right_door=Waypoint((517.9, 636.5)))
        item_X502Y605 = Waypoint((502.6, 605.0))
        enemy = Waypoint((519.0, 623.0))
        # ===== End of generated waypoints =====

        self.minimap.lock_rotation(151)
        self.clear_item(item_X502Y605)
        self.clear_enemy(enemy)

    def Luofu_StargazerNavalia_F1_X521Y447(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((521.4, 447.5)), | 188.1     | 181      |
        | enemy    | Waypoint((521.2, 507.2)), | 98.8      | 186      |
        | exit_    | Waypoint((521.2, 507.2)), | 98.8      | 186      |
        | exit1    | Waypoint((530.8, 514.9)), | 183.8     | 181      |
        | exit2    | Waypoint((514.8, 514.8)), | 183.8     | 181      |
        """
        self.map_init(plane=Luofu_StargazerNavalia, floor="F1", position=(521.4, 447.5))
        self.register_domain_exit(
            Waypoint((521.2, 507.2)), end_rotation=186,
            left_door=Waypoint((530.8, 514.9)), right_door=Waypoint((514.8, 514.8)))
        enemy = Waypoint((521.2, 507.2))
        # ===== End of generated waypoints =====

        self.minimap.lock_rotation(180)
        self.clear_enemy(enemy)
