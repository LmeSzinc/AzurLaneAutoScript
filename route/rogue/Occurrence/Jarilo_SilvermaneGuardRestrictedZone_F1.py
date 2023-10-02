from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_SilvermaneGuardRestrictedZone
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_SilvermaneGuardRestrictedZone_F1_X377Y505(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((377.4, 505.6)), | 96.7      | 91       |
        | item     | Waypoint((397.0, 514.4)), | 119.8     | 117      |
        | event    | Waypoint((422.2, 506.4)), | 92.7      | 84       |
        | exit     | Waypoint((423.8, 505.7)), | 96.8      | 91       |
        """
        self.map_init(plane=Jarilo_SilvermaneGuardRestrictedZone, floor="F1", position=(377.4, 505.6))
        self.register_domain_exit(Waypoint((423.8, 505.7)), end_rotation=91)
        item = Waypoint((397.0, 514.4))
        event = Waypoint((422.2, 506.4))

        self.clear_item(item)
        self.clear_event(event)
        # ===== End of generated waypoints =====

    def Jarilo_SilvermaneGuardRestrictedZone_F1_X439Y237(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((439.3, 237.1)), | 354.1     | 348      |
        | item     | Waypoint((440.8, 215.2)), | 15.6      | 11       |
        | event    | Waypoint((434.8, 192.4)), | 355.9     | 359      |
        | exit     | Waypoint((428.6, 190.4)), | 76.4      | 338      |
        """
        self.map_init(plane=Jarilo_SilvermaneGuardRestrictedZone, floor="F1", position=(439.3, 237.1))
        self.register_domain_exit(Waypoint((428.6, 190.4)), end_rotation=338)
        item = Waypoint((440.8, 215.2))
        event = Waypoint((434.8, 192.4))

        self.clear_item(item)
        self.clear_event(event)
        # ===== End of generated waypoints =====
