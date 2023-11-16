from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_AlchemyCommission
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_AlchemyCommission_F2_X681Y625(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((680.9, 625.9)), | 146.7     | 140      |
        | item     | Waypoint((688.4, 642.0)), | 148.8     | 140      |
        | herta    | Waypoint((708.9, 664.4)), | 148.4     | 140      |
        | exit_    | Waypoint((725.2, 667.3)), | 148.8     | 140      |
        """
        self.map_init(plane=Luofu_AlchemyCommission, floor="F2", position=(680.9, 625.9))
        item = Waypoint((688.4, 642.0))
        herta = Waypoint((708.9, 664.4))
        exit_ = Waypoint((725.2, 667.3))

        self.clear_item(item)
        self.domain_herta(herta)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====

    def Luofu_AlchemyCommission_F2_X685Y629(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((680.9, 625.9)), | 146.7     | 140      |
        | item     | Waypoint((688.4, 642.0)), | 148.8     | 140      |
        | herta    | Waypoint((708.9, 664.4)), | 148.4     | 140      |
        | exit_    | Waypoint((725.2, 667.3)), | 148.8     | 140      |
        """
        self.map_init(plane=Luofu_AlchemyCommission, floor="F2", position=(685, 629))
        item = Waypoint((688.4, 642.0))
        herta = Waypoint((708.9, 664.4))
        exit_ = Waypoint((725.2, 667.3))

        self.clear_item(item)
        self.domain_herta(herta)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====

        # Same as Luofu_AlchemyCommission_F2_X681Y625
