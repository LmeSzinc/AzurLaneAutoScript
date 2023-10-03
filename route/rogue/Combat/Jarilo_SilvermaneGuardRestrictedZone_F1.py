from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_SilvermaneGuardRestrictedZone
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_SilvermaneGuardRestrictedZone_F1_X221Y426(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((221.3, 426.1)), | 274.2     | 274      |
        | item     | Waypoint((195.9, 434.9)), | 237.2     | 234      |
        | enemy    | Waypoint((172.9, 425.9)), | 274.2     | 274      |
        | exit     | Waypoint((172.9, 425.9)), | 274.2     | 274      |
        """
        self.map_init(plane=Jarilo_SilvermaneGuardRestrictedZone, floor="F1", position=(221.3, 426.1))
        self.register_domain_exit(Waypoint((172.9, 425.9)), end_rotation=274)
        item = Waypoint((195.9, 434.9))
        enemy = Waypoint((172.9, 425.9))
        # ===== End of generated waypoints =====

        self.clear_item(item)
        self.clear_enemy(enemy)

    def Jarilo_SilvermaneGuardRestrictedZone_F1_X421Y173(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((421.5, 173.4)), | 172.8     | 165      |
        | item     | Waypoint((418.5, 218.3)), | 183.8     | 181      |
        | enemy    | Waypoint((440.2, 232.4)), | 166.6     | 154      |
        | exit     | Waypoint((440.2, 232.4)), | 166.6     | 154      |
        """
        self.map_init(plane=Jarilo_SilvermaneGuardRestrictedZone, floor="F1", position=(421.5, 173.4))
        self.register_domain_exit(Waypoint((440.2, 232.4)), end_rotation=154)
        item = Waypoint((418.5, 218.3))
        enemy = Waypoint((440.2, 232.4))
        # ===== End of generated waypoints =====

        self.clear_item(item)
        self.clear_enemy(enemy)

    def Jarilo_SilvermaneGuardRestrictedZone_F1_X547Y467(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((547.1, 467.0)), | 190.1     | 184      |
        | item1    | Waypoint((562.4, 528.4)), | 203.1     | 200      |
        | enemy1   | Waypoint((566.2, 572.0)), | 282.8     | 181      |
        | item2    | Waypoint((574.0, 583.2)), | 139.4     | 140      |
        | enemy3   | Waypoint((542.6, 613.0)), | 239.8     | 237      |
        | enemy4   | Waypoint((494.2, 611.8)), | 274.2     | 274      |
        | item3    | Waypoint((536.4, 628.1)), | 210.2     | 204      |
        | exit     | Waypoint((494.2, 611.8)), | 274.2     | 274      |
        """
        self.map_init(plane=Jarilo_SilvermaneGuardRestrictedZone, floor="F1", position=(547.1, 467.0))
        self.register_domain_exit(Waypoint((494.2, 611.8)), end_rotation=274)
        item1 = Waypoint((562.4, 528.4))
        enemy1 = Waypoint((566.2, 572.0))
        item2 = Waypoint((574.0, 583.2))
        enemy3 = Waypoint((542.6, 613.0))
        enemy4 = Waypoint((494.2, 611.8))
        item3 = Waypoint((536.4, 628.1))
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
            enemy4.straight_run(),
        )
