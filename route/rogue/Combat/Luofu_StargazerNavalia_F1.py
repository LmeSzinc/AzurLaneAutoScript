from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_StargazerNavalia
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_StargazerNavalia_F1_X183Y315(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((183.4, 315.6)), | 98.9      | 89       |
        | item     | Waypoint((208.5, 306.1)), | 82.5      | 80       |
        | enemy    | Waypoint((247.4, 320.2)), | 114.1     | 112      |
        | exit     | Waypoint((701.4, 523.4)), | 274.2     | 89       |
        """
        self.map_init(plane=Luofu_StargazerNavalia, floor="F1", position=(183.4, 315.6))
        self.register_domain_exit(Waypoint((701.4, 523.4)), end_rotation=89)
        item = Waypoint((208.5, 306.1))
        enemy = Waypoint((247.4, 320.2))
        # ===== End of generated waypoints =====

        self.clear_item(item)
        self.clear_enemy(enemy)

    def Luofu_StargazerNavalia_F1_X215Y192(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((215.5, 192.6)), | 190.1     | 184      |
        | item1    | Waypoint((212.0, 241.6)), | 194.8     | 204      |
        | enemy1   | Waypoint((188.6, 248.2)), | 223.8     | 221      |
        | node2    | Waypoint((178.9, 278.9)), | 198.7     | 195      |
        | node3    | Waypoint((180.1, 299.2)), | 187.0     | 181      |
        | enemy3   | Waypoint((247.6, 317.2)), | 198.7     | 96       |
        | exit     | Waypoint((247.6, 317.2)), | 198.7     | 96       |
        """
        self.map_init(plane=Luofu_StargazerNavalia, floor="F1", position=(215.5, 192.6))
        self.register_domain_exit(Waypoint((247.6, 317.2)), end_rotation=96)
        item1 = Waypoint((212.0, 241.6))
        enemy1 = Waypoint((188.6, 248.2))
        node2 = Waypoint((178.9, 278.9))
        node3 = Waypoint((180.1, 299.2))
        enemy3 = Waypoint((247.6, 317.2))
        # ===== End of generated waypoints =====

        # Ignore items
        self.clear_enemy(enemy1.straight_run())
        # Ignore enemy2
        self.clear_enemy(
            node2.straight_run(),
            node3.straight_run(),
            enemy3.straight_run(),
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
        | enemy3         | Waypoint((556.5, 599.8)), | 96.8      | 96       |
        | exit           | Waypoint((559.5, 601.5)), | 129.8     | 94       |
        """
        self.map_init(plane=Luofu_StargazerNavalia, floor="F1", position=(432.7, 593.4))
        self.register_domain_exit(Waypoint((559.5, 601.5)), end_rotation=94)
        event = Waypoint((449.6, 606.4))
        item1_X464Y586 = Waypoint((464.6, 586.5))
        enemy1 = Waypoint((506.2, 596.2))
        item2 = Waypoint((522.8, 589.0))
        enemy3 = Waypoint((556.5, 599.8))
        # ===== End of generated waypoints =====

        # Ignore items
        self.clear_enemy(enemy1)
        # Ignore enemy2
        self.clear_enemy(enemy3)

    def Luofu_StargazerNavalia_F1_X499Y581(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((499.6, 581.5)), | 157.2     | 151      |
        | item     | Waypoint((499.1, 608.9)), | 180.0     | 179      |
        | enemy    | Waypoint((519.0, 623.0)), | 149.8     | 149      |
        | exit     | Waypoint((524.4, 624.7)), | 166.7     | 161      |
        """
        self.map_init(plane=Luofu_StargazerNavalia, floor="F1", position=(499.6, 581.5))
        self.register_domain_exit(Waypoint((524.4, 624.7)), end_rotation=161)
        item = Waypoint((499.1, 608.9))
        enemy = Waypoint((519.0, 623.0))
        # ===== End of generated waypoints =====

        self.clear_item(item)
        self.clear_enemy(enemy)
