from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_Cloudford
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_Cloudford_F2_X425Y171(self):
        """
        | Waypoint    | Position                  | Direction | Rotation |
        | ----------- | ------------------------- | --------- | -------- |
        | spawn       | Waypoint((425.5, 171.6)), | 190.1     | 184      |
        | item1       | Waypoint((436.8, 203.6)), | 166.7     | 161      |
        | item2       | Waypoint((407.1, 205.3)), | 181.3     | 177      |
        | enemy2right | Waypoint((407.2, 253.0)), | 311.8     | 274      |
        | enemy2left  | Waypoint((435.0, 254.6)), | 181.3     | 174      |
        | item3       | Waypoint((382.4, 275.3)), | 250.8     | 251      |
        | enemy3      | Waypoint((318.8, 267.0)), | 279.8     | 281      |
        | exit        | Waypoint((324.8, 268.5)), | 283.0     | 278      |
        """
        self.map_init(plane=Luofu_Cloudford, floor="F2", position=(425.5, 171.6))
        self.register_domain_exit(Waypoint((324.8, 268.5)), end_rotation=278)
        item1 = Waypoint((436.8, 203.6))
        item2 = Waypoint((407.1, 205.3))
        enemy2right = Waypoint((407.2, 253.0))
        enemy2left = Waypoint((435.0, 254.6))
        item3 = Waypoint((382.4, 275.3))
        enemy3 = Waypoint((318.8, 267.0))
        # ===== End of generated waypoints =====

        # Items are randomly generated in 4 position, ignore all
        # self.clear_item(item1)
        # self.clear_item(item2)
        self.clear_enemy(
            enemy2left,
            enemy2right.straight_run(),
        )
        # 3
        # self.clear_item(item3.straight_run())
        self.clear_enemy(
            enemy2right,
            enemy3.straight_run()
        )
