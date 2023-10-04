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
