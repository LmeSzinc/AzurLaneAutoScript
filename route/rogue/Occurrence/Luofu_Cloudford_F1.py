from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_Cloudford
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_Cloudford_F1_X241Y947(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((241.4, 947.5)), | 274.2     | 274      |
        | event    | Waypoint((199.0, 940.8)), | 300.1     | 294      |
        | exit     | Waypoint((193.1, 947.2)), | 12.8      | 274      |
        """
        self.map_init(plane=Luofu_Cloudford, floor="F1", position=(241.4, 947.5))
        self.register_domain_exit(Waypoint((193.1, 947.2)), end_rotation=274)
        event = Waypoint((199.0, 940.8))

        self.clear_event(event)
        # ===== End of generated waypoints =====

    def Luofu_Cloudford_F1_X283Y865(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((283.2, 865.2)), | 6.7       | 4        |
        | item     | Waypoint((272.2, 840.2)), | 332.7     | 327      |
        | event    | Waypoint((291.8, 822.2)), | 26.8      | 22       |
        | exit     | Waypoint((285.3, 818.1)), | 99.0      | 1        |
        """
        self.map_init(plane=Luofu_Cloudford, floor="F1", position=(283.2, 865.2))
        self.register_domain_exit(Waypoint((285.3, 818.1)), end_rotation=1)
        item = Waypoint((272.2, 840.2))
        event = Waypoint((291.8, 822.2))

        self.clear_item(item)
        self.clear_event(event)
        # ===== End of generated waypoints =====
