from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_RivetTown
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_RivetTown_F1_X157Y273(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((157.2, 273.5)), | 60.8      | 59       |
        | item     | Waypoint((174.9, 274.8)), | 96.8      | 89       |
        | herta    | Waypoint((202.2, 259.4)), | 76.3      | 73       |
        | exit     | Waypoint((208.6, 244.6)), | 67.1      | 61       |
        """
        self.map_init(plane=Jarilo_RivetTown, floor="F1", position=(157.2, 273.5))
        item = Waypoint((174.9, 274.8))
        herta = Waypoint((202.2, 259.4))
        exit_ = Waypoint((208.6, 244.6))

        self.clear_item(item)
        self.domain_herta(herta)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====
