from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Herta_SupplyZone
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Herta_SupplyZone_F2Rogue_X397Y227(self):
        """
        | Waypoint       | Position                  | Direction | Rotation |
        | -------------- | ------------------------- | --------- | -------- |
        | spawn          | Waypoint((397.4, 223.3)), | 6.7       | 4        |
        | node_X397Y227  | Waypoint((400.5, 184.8)), | 15.6      | 11       |
        | event_X397Y227 | Waypoint((404.5, 182.1)), | 26.8      | 24       |
        | exit_X397Y227  | Waypoint((398.8, 176.6)), | 4.2       | 1        |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2", position=(397.4, 223.3))
        self.register_domain_exit(Waypoint((398.8, 176.6)), end_rotation=1)
        node_X397Y227 = Waypoint((400.5, 184.8))
        event_X397Y227 = Waypoint((404.5, 182.1))

        self.clear_event(event_X397Y227)
        # ===== End of generated waypoints =====
