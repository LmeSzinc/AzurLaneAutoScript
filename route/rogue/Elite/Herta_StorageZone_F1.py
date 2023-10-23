from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Herta_StorageZone
from tasks.map.route.base import locked_position
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    @locked_position
    def Herta_StorageZone_F1_X477Y233(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((477.6, 233.5)), | 319.8     | 320      |
        | enemy    | Waypoint((444.7, 197.9)), | 318.0     | 318      |
        | reward   | Waypoint((442.6, 186.3)), | 356.3     | 354      |
        | exit     | Waypoint((431.1, 194.6)), | 290.1     | 290      |
        """
        self.map_init(plane=Herta_StorageZone, floor="F1", position=(477.6, 233.5))
        enemy = Waypoint((444.7, 197.9))
        reward = Waypoint((442.6, 186.3))
        exit_ = Waypoint((431.1, 194.6))

        self.clear_elite(enemy)
        self.domain_reward(reward)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====
