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
