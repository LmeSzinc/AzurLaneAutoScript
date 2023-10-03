from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Herta_StorageZone
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Herta_StorageZone_F1_X703Y267(self):
        """
        | Waypoint      | Position                  | Direction | Rotation |
        | ------------- | ------------------------- | --------- | -------- |
        | spawn         | Waypoint((703.2, 267.6)), | 300.1     | 292      |
        | item_X690Y255 | Waypoint((690.6, 255.0)), | 327.8     | 322      |
        | herta         | Waypoint((660.9, 244.9)), | 311.8     | 308      |
        | exit          | Waypoint((645.3, 251.4)), | 294.6     | 292      |
        """
        self.map_init(plane=Herta_StorageZone, floor="F1", position=(703.2, 267.6))
        item_X690Y255 = Waypoint((690.6, 255.0))
        herta = Waypoint((660.9, 244.9))
        exit_ = Waypoint((645.3, 251.4))

        self.clear_item(item_X690Y255)
        self.domain_herta(herta)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====
