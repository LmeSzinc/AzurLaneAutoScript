from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Herta_SupplyZone
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Herta_SupplyZone_F2Rogue_X215Y112(self):
        """
        | Waypoint      | Position                  | Direction | Rotation |
        | ------------- | ------------------------- | --------- | -------- |
        | spawn         | Waypoint((219.6, 112.8)), | 96.7      | 91       |
        | item_X227Y105 | Waypoint((227.4, 105.1)), | 67.2      | 61       |
        | enemy         | Waypoint((264.2, 114.1)), | 101.1     | 98       |
        | exit_X227Y105 | Waypoint((266.7, 113.7)), | 60.8      | 91       |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2Rogue", position=(219.6, 112.8))
        self.register_domain_exit(Waypoint((266.7, 113.7)), end_rotation=91)
        item_X227Y105 = Waypoint((227.4, 105.1))
        enemy = Waypoint((264.2, 114.1))
        # ===== End of generated waypoints =====

        self.clear_item(item_X227Y105)
        self.clear_enemy(enemy)
