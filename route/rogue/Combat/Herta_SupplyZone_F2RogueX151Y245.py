from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Herta_SupplyZone
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Herta_SupplyZone_F2RogueX151Y245_X151Y245(self):
        """
        | Waypoint        | Position                  | Direction | Rotation |
        | --------------- | ------------------------- | --------- | -------- |
        | spawn           | Waypoint((152.0, 245.4)), | 190.1     | 184      |
        | node1           | Waypoint((156.1, 286.2)), | 166.8     | 163      |
        | bridge_center   | Waypoint((222.2, 246.8)), | 6.7       | 4        |
        | enemy2          | Waypoint((222.0, 234.6)), | 11.2      | 184      |
        | bridge1         | Waypoint((222.8, 284.9)), | 6.7       | 4        |
        | node3_X222Y178  | Waypoint((222.8, 178.8)), | 6.7       | 4        |
        | node2_X244Y298  | Waypoint((244.4, 298.3)), | 105.5     | 101      |
        | enemy3_X283Y178 | Waypoint((283.3, 178.9)), | 2.7       | 89       |
        | exit_X283Y178   | Waypoint((283.3, 178.9)), | 2.7       | 89       |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2RogueX151Y245", position=(152.0, 245.4))
        self.register_domain_exit(Waypoint((283.3, 178.9)), end_rotation=89)
        node1 = Waypoint((156.1, 286.2))
        bridge_center = Waypoint((222.2, 246.8))
        enemy2 = Waypoint((222.0, 234.6))
        bridge1 = Waypoint((222.8, 284.9))
        node3_X222Y178 = Waypoint((222.8, 178.8))
        node2_X244Y298 = Waypoint((244.4, 298.3))
        enemy3_X283Y178 = Waypoint((283.3, 178.9))
        # ===== End of generated waypoints =====

        # 1
        self.clear_enemy(
            node1,
            node2_X244Y298.straight_run(),
        )
        self.clear_item(node2_X244Y298),
        # 2 Go through bridge
        self.rotation_set(0)
        self.clear_enemy(
            bridge1.set_threshold(5),
            bridge_center.set_threshold(3),
            enemy2,
        )
        # 3
        self.clear_item(
            bridge_center.set_threshold(3),
            node3_X222Y178,
        )
        self.clear_enemy(
            node3_X222Y178.set_threshold(5),
            enemy3_X283Y178.straight_run(),
        )
