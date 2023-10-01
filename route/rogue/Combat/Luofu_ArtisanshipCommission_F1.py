from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_ArtisanshipCommission
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_ArtisanshipCommission_F1_X185Y361(self):
        """
        | Waypoint       | Position                  | Direction | Rotation |
        | -------------- | ------------------------- | --------- | -------- |
        | spawn          | Waypoint((185.4, 361.4)), | 157.2     | 151      |
        | enemy_X212Y398 | Waypoint((212.5, 398.4)), | 149.9     | 327      |
        | item           | Waypoint((232.4, 388.4)), | 129.9     | 133      |
        | exit           | Waypoint((217.4, 405.1)), | 166.7     | 168      |
        """
        self.map_init(plane=Luofu_ArtisanshipCommission, floor="F1", position=(185.4, 361.4))
        self.register_domain_exit(Waypoint((217.4, 405.1)), end_rotation=168)
        enemy_X212Y398 = Waypoint((212.5, 398.4))
        item = Waypoint((232.4, 388.4))
        # ===== End of generated waypoints =====

        # Enemy first, then go back for item
        self.clear_enemy(enemy_X212Y398)
        self.clear_item(item)

    def Luofu_ArtisanshipCommission_F1_X655Y537(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((655.5, 537.3)), | 6.7       | 361      |
        | item     | Waypoint((680.6, 503.2)), | 30.1      | 27       |
        | enemy    | Waypoint((656.2, 484.2)), | 11.1      | 184      |
        | exit     | Waypoint((647.0, 477.5)), | 357.8     | 352      |
        """
        self.map_init(plane=Luofu_ArtisanshipCommission, floor="F1", position=(655.5, 537.3))
        self.register_domain_exit(Waypoint((647.0, 477.5)), end_rotation=352)
        item = Waypoint((680.6, 503.2))
        enemy = Waypoint((656.2, 484.2))
        # ===== End of generated waypoints =====

        # Ignore item, bad way
        self.clear_enemy(enemy)
