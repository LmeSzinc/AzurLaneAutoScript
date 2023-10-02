from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Herta_StorageZone
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Herta_StorageZone_F2_X365Y167(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((363.4, 166.9)), | 274.2     | 274      |
        | item     | Waypoint((332.8, 172.0)), | 263.8     | 260      |
        | event    | Waypoint((318.9, 155.2)), | 290.1     | 285      |
        | exit     | Waypoint((298.5, 162.7)), | 271.8     | 269      |
        """
        self.map_init(plane=Herta_StorageZone, floor="F2", position=(363.4, 166.9))
        self.register_domain_exit(Waypoint((298.5, 162.7)), end_rotation=269)
        item = Waypoint((332.8, 172.0))
        event = Waypoint((318.9, 155.2))

        self.clear_item(item)
        self.clear_event(event)
        # ===== End of generated waypoints =====
