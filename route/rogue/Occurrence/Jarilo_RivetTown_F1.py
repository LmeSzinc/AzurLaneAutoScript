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
        | exit     | Waypoint((211.2, 435.4)), | 96.7      | 91       |
        """
        self.map_init(plane=Jarilo_RivetTown, floor="F1", position=(157.4, 435.5))
        self.register_domain_exit(Waypoint((211.2, 435.4)), end_rotation=91)
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
        | exit     | Waypoint((208.3, 349.2)), | 12.7      | 1        |
        """
        self.map_init(plane=Jarilo_RivetTown, floor="F1", position=(209.3, 397.9))
        self.register_domain_exit(Waypoint((208.3, 349.2)), end_rotation=1)
        item = Waypoint((220.9, 378.0))
        event = Waypoint((218.0, 356.2))

        self.clear_item(item)
        self.clear_event(event)
        # ===== End of generated waypoints =====
