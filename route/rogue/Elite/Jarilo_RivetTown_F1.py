from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_RivetTown
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_RivetTown_F1_X149Y435(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((149.9, 435.6)), | 96.7      | 91       |
        | enemy    | Waypoint((197.4, 437.1)), | 96.8      | 94       |
        | reward   | Waypoint((208.4, 441.0)), | 102.9     | 98       |
        | exit     | Waypoint((216.4, 428.6)), | 96.7      | 94       |
        """
        self.map_init(plane=Jarilo_RivetTown, floor="F1", position=(149.9, 435.6))
        enemy = Waypoint((197.4, 437.1))
        reward = Waypoint((208.4, 441.0))
        exit_ = Waypoint((216.4, 428.6))

        self.clear_elite(enemy)
        self.domain_reward(reward)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====
