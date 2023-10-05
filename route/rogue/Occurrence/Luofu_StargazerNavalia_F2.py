from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_StargazerNavalia
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_StargazerNavalia_F2_X579Y183(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((579.8, 183.5)), | 96.7      | 91       |
        | event    | Waypoint((482.9, 204.6)), | 105.5     | 114      |
        | exit     | Waypoint((622.1, 186.3)), | 96.7      | 91       |
        """
        self.map_init(plane=Luofu_StargazerNavalia, floor="F2", position=(579.8, 183.5))
        self.register_domain_exit(Waypoint((622.1, 186.3)), end_rotation=91)
        event = Waypoint((482.9, 204.6))

        self.clear_event(event)
        # ===== End of generated waypoints =====
