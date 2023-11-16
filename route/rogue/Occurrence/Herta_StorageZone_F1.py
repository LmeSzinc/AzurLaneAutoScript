from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Herta_StorageZone
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Herta_StorageZone_F1_X273Y93(self):
        """
        | Waypoint | Position                 | Direction | Rotation |
        | -------- | ------------------------ | --------- | -------- |
        | spawn    | Waypoint((273.5, 93.2)), | 308.0     | 304      |
        | event    | Waypoint((238.4, 64.8)), | 324.9     | 311      |
        | exit_    | Waypoint((227.8, 69.5)), | 30.2      | 299      |
        | exit1    | Waypoint((218.2, 74.8)), | 303.8     | 301      |
        | exit2    | Waypoint((225.8, 60.2)), | 303.8     | 301      |
        """
        self.map_init(plane=Herta_StorageZone, floor="F1", position=(273.5, 93.2))
        self.register_domain_exit(
            Waypoint((227.8, 69.5)), end_rotation=299,
            left_door=Waypoint((218.2, 74.8)), right_door=Waypoint((225.8, 60.2)))
        event = Waypoint((238.4, 64.8))

        self.clear_event(event)
        # ===== End of generated waypoints =====
