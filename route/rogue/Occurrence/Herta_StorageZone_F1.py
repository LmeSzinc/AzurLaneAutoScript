from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Herta_StorageZone
from tasks.map.route.base import locked_position
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

    @locked_position
    def Herta_StorageZone_F1_X281Y164(self):
        """
        | Waypoint       | Position                  | Direction | Rotation |
        | -------------- | ------------------------- | --------- | -------- |
        | spawn          | Waypoint((281.1, 164.2)), | 282.3     | 274      |
        | event          | Waypoint((236.6, 159.2)), | 282.9     | 269      |
        | exit_          | Waypoint((231.5, 165.6)), | 281.8     | 274      |
        | exit1_X225Y170 | Waypoint((225.3, 169.8)), | 281.8     | 274      |
        | exit2          | Waypoint((223.5, 159.4)), | 275.8     | 269      |
        """
        self.map_init(plane=Herta_StorageZone, floor="F1", position=(281.1, 164.2))
        self.register_domain_exit(
            Waypoint((231.5, 165.6)), end_rotation=274,
            left_door=Waypoint((225.3, 169.8)), right_door=Waypoint((223.5, 159.4)))
        event = Waypoint((236.6, 159.2))

        self.clear_event(event)
        # ===== End of generated waypoints =====
