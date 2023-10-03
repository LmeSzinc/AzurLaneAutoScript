from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_CorridorofFadingEchoes
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_CorridorofFadingEchoes_F1_X291Y765(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((291.1, 765.3)), | 190.1     | 184      |
        | item     | Waypoint((282.1, 782.4)), | 216.3     | 211      |
        | enemy    | Waypoint((291.2, 821.2)), | 188.1     | 181      |
        | exit     | Waypoint((291.2, 821.2)), | 188.1     | 181      |
        """
        self.map_init(plane=Jarilo_CorridorofFadingEchoes, floor="F1", position=(291.1, 765.3))
        self.register_domain_exit(Waypoint((291.2, 821.2)), end_rotation=181)
        item = Waypoint((282.1, 782.4))
        enemy = Waypoint((291.2, 821.2))
        # ===== End of generated waypoints =====

        self.clear_item(item)
        self.clear_enemy(enemy)

    def Jarilo_CorridorofFadingEchoes_F1_X319Y949(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((319.4, 949.3)), | 96.7      | 91       |
        | item     | Waypoint((340.4, 940.6)), | 59.1      | 54       |
        | enemy    | Waypoint((380.2, 948.0)), | 261.8     | 73       |
        | exit     | Waypoint((386.2, 944.2)), | 96.7      | 89       |
        """
        self.map_init(plane=Jarilo_CorridorofFadingEchoes, floor="F1", position=(319.4, 949.3))
        self.register_domain_exit(Waypoint((386.2, 944.2)), end_rotation=89)
        item = Waypoint((340.4, 940.6))
        enemy = Waypoint((380.2, 948.0))
        # ===== End of generated waypoints =====

        # Ignore item, bad way
        self.clear_enemy(enemy)
