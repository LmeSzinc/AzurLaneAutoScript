from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_RivetTown
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_RivetTown_F1_X157Y435(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((157.4, 435.5)), | 96.7      | 91       |
        | event    | Waypoint((200.4, 426.5)), | 76.4      | 73       |
        | exit_    | Waypoint((211.2, 435.4)), | 96.7      | 91       |
        | exit1    | Waypoint((216.4, 428.6)), | 97.9      | 91       |
        | exit2    | Waypoint((218.0, 442.4)), | 101.1     | 91       |
        """
        self.map_init(plane=Jarilo_RivetTown, floor="F1", position=(157.4, 435.5))
        self.register_domain_exit(
            Waypoint((211.2, 435.4)), end_rotation=91,
            left_door=Waypoint((216.4, 428.6)), right_door=Waypoint((218.0, 442.4)))
        event = Waypoint((200.4, 426.5))

        self.clear_event(event)
        # ===== End of generated waypoints =====

    def Jarilo_RivetTown_F1_X209Y398(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((209.3, 397.9)), | 6.7       | 4        |
        | item     | Waypoint((220.9, 378.0)), | 36.2      | 34       |
        | event    | Waypoint((218.0, 356.2)), | 12.7      | 8        |
        | exit_    | Waypoint((208.3, 349.2)), | 12.7      | 1        |
        | exit1    | Waypoint((203.4, 343.2)), | 2.8       | 357      |
        | exit2    | Waypoint((216.8, 341.5)), | 25.6      | 27       |
        """
        self.map_init(plane=Jarilo_RivetTown, floor="F1", position=(209.3, 397.9))
        self.register_domain_exit(
            Waypoint((208.3, 349.2)), end_rotation=1,
            left_door=Waypoint((203.4, 343.2)), right_door=Waypoint((216.8, 341.5)))
        item = Waypoint((220.9, 378.0))
        event = Waypoint((218.0, 356.2))

        self.clear_item(item)
        self.clear_event(event)
        # ===== End of generated waypoints =====

    def Jarilo_RivetTown_F1_X289Y97(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((290.1, 97.5)),  | 249.2     | 244      |
        | item     | Waypoint((285.0, 122.6)), | 254.1     | 248      |
        | event    | Waypoint((255.5, 112.9)), | 252.7     | 251      |
        | exit_    | Waypoint((251.0, 123.3)), | 247.3     | 239      |
        | exit1    | Waypoint((246.4, 130.8)), | 249.0     | 239      |
        | exit2    | Waypoint((243.8, 120.1)), | 247.3     | 241      |
        """
        self.map_init(plane=Jarilo_RivetTown, floor="F1", position=(290.1, 97.5))
        self.register_domain_exit(
            Waypoint((251.0, 123.3)), end_rotation=239,
            left_door=Waypoint((246.4, 130.8)), right_door=Waypoint((243.8, 120.1)))
        item = Waypoint((285.0, 122.6))
        event = Waypoint((255.5, 112.9))

        self.clear_item(item)
        self.clear_event(event)
        # ===== End of generated waypoints =====
