from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_ArtisanshipCommission
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_ArtisanshipCommission_F1_X506Y495(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((506.0, 495.4)), | 96.7      | 91       |
        | enemy    | Waypoint((554.0, 492.2)), | 96.7      | 91       |
        | reward   | Waypoint((564.8, 498.9)), | 134.2     | 128      |
        | exit     | Waypoint((572.8, 482.4)), | 76.4      | 68       |
        """
        self.map_init(plane=Luofu_ArtisanshipCommission, floor="F1", position=(506.0, 495.4))
        enemy = Waypoint((554.0, 492.2))
        reward = Waypoint((564.8, 498.9))
        exit_ = Waypoint((572.8, 482.4))

        self.clear_elite(enemy)
        self.domain_reward(reward)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====
