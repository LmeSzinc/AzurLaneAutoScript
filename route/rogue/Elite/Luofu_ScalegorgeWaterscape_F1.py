from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_ScalegorgeWaterscape
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_ScalegorgeWaterscape_F1_X1368Y261(self):
        """
        | Waypoint | Position                   | Direction | Rotation |
        | -------- | -------------------------- | --------- | -------- |
        | spawn    | Waypoint((1368.9, 261.5)), | 96.7      | 91       |
        | enemy    | Waypoint((1402.5, 260.6)), | 96.8      | 91       |
        | reward   | Waypoint((1408.8, 266.8)), | 135.8     | 133      |
        | exit     | Waypoint((1415.0, 255.4)), | 67.2      | 64       |
        """
        self.map_init(plane=Luofu_ScalegorgeWaterscape, floor="F1", position=(1368.9, 261.5))
        enemy = Waypoint((1402.5, 260.6))
        reward = Waypoint((1408.8, 266.8))
        exit_ = Waypoint((1415.0, 255.4))

        self.clear_elite(enemy)
        self.domain_reward(reward)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====
