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
        | exit_    | Waypoint((193.1, 947.2)), | 12.8      | 274      |
        | exit1    | Waypoint((179.0, 956.4)), | 279.8     | 278      |
        | exit2    | Waypoint((184.1, 940.2)), | 282.9     | 278      |
        """
        self.map_init(plane=Luofu_Cloudford, floor="F1", position=(241.4, 947.5))
        self.register_domain_exit(
            Waypoint((193.1, 947.2)), end_rotation=274,
            left_door=Waypoint((179.0, 956.4)), right_door=Waypoint((184.1, 940.2)))
        event = Waypoint((199.0, 940.8))

        self.clear_event(event)
        # ===== End of generated waypoints =====

    def Luofu_Cloudford_F1_X281Y873(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((283.2, 865.2)), | 6.7       | 4        |
        | item     | Waypoint((272.2, 840.2)), | 332.7     | 327      |
        | event    | Waypoint((291.8, 822.2)), | 26.8      | 22       |
        | exit_    | Waypoint((285.3, 818.1)), | 99.0      | 1        |
        | exit1    | Waypoint((276.2, 807.8)), | 4.4       | 4        |
        | exit2    | Waypoint((290.4, 810.2)), | 4.3       | 4        |
        """
        self.map_init(plane=Luofu_Cloudford, floor="F1", position=(281, 873))
        self.register_domain_exit(
            Waypoint((285.3, 818.1)), end_rotation=1,
            left_door=Waypoint((276.2, 807.8)), right_door=Waypoint((290.4, 810.2)))
        item = Waypoint((272.2, 840.2))
        event = Waypoint((291.8, 822.2))

        self.clear_item(item)
        self.clear_event(event)
        # ===== End of generated waypoints =====

        """
        Notes
        Luofu_Cloudford_F1_X281Y873 is the same as Luofu_Cloudford_F1_X283Y865
        but for wrong spawn point detected
        """

    def Luofu_Cloudford_F1_X283Y865(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((283.2, 865.2)), | 6.7       | 4        |
        | item     | Waypoint((272.2, 840.2)), | 332.7     | 327      |
        | event    | Waypoint((291.8, 822.2)), | 26.8      | 22       |
        | exit_    | Waypoint((285.3, 818.1)), | 99.0      | 1        |
        | exit1    | Waypoint((276.2, 807.8)), | 4.4       | 4        |
        | exit2    | Waypoint((290.4, 810.2)), | 4.3       | 4        |
        """
        self.map_init(plane=Luofu_Cloudford, floor="F1", position=(283.2, 865.2))
        self.register_domain_exit(
            Waypoint((285.3, 818.1)), end_rotation=1,
            left_door=Waypoint((276.2, 807.8)), right_door=Waypoint((290.4, 810.2)))
        item = Waypoint((272.2, 840.2))
        event = Waypoint((291.8, 822.2))

        self.clear_item(item)
        self.clear_event(event)
        # ===== End of generated waypoints =====

    def Luofu_Cloudford_F1_X537Y373(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((537.4, 373.3)), | 96.7      | 91       |
        | item     | Waypoint((567.0, 346.6)), | 96.7      | 91       |
        | event    | Waypoint((580.8, 363.0)), | 94.2      | 91       |
        | exit_    | Waypoint((588.6, 372.8)), | 282.4     | 89       |
        | exit1    | Waypoint((595.5, 365.6)), | 96.8      | 87       |
        | exit2    | Waypoint((595.3, 379.7)), | 96.8      | 87       |
        """
        self.map_init(plane=Luofu_Cloudford, floor="F1", position=(537.4, 373.3))
        self.register_domain_exit(
            Waypoint((588.6, 372.8)), end_rotation=89,
            left_door=Waypoint((595.5, 365.6)), right_door=Waypoint((595.3, 379.7)))
        item = Waypoint((567.0, 346.6))
        event = Waypoint((580.8, 363.0))

        self.clear_item(item)
        self.clear_event(event)
        # ===== End of generated waypoints =====
