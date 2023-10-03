from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_CorridorofFadingEchoes
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_CorridorofFadingEchoes_F1_X291Y653(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((291.7, 653.4)), | 190.1     | 184      |
        | item     | Waypoint((280.6, 668.6)), | 210.2     | 198      |
        | herta    | Waypoint((284.0, 702.2)), | 182.8     | 188      |
        | exit     | Waypoint((293.2, 719.4)), | 282.9     | 343      |
        """
        self.map_init(plane=Jarilo_CorridorofFadingEchoes, floor="F1", position=(291.7, 653.4))
        item = Waypoint((280.6, 668.6))
        herta = Waypoint((284.0, 702.2))
        exit_ = Waypoint((293.2, 719.4))

        self.clear_item(item)
        self.domain_herta(herta)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====
