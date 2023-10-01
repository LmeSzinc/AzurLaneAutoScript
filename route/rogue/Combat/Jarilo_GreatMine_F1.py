from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_GreatMine
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_GreatMine_F1_X133Y465(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((133.3, 465.6)), | 334.8     | 331      |
        | item     | Waypoint((108.7, 448.2)), | 318.0     | 320      |
        | enemy    | Waypoint((110.1, 420.6)), | 337.4     | 338      |
        | exit     | Waypoint((104.0, 414.0)), | 334.8     | 331      |
        """
        self.map_init(plane=Jarilo_GreatMine, floor="F1", position=(133.3, 465.6))
        self.register_domain_exit(Waypoint((104.0, 414.0)), end_rotation=331)
        item = Waypoint((108.7, 448.2))
        enemy = Waypoint((110.1, 420.6))
        # ===== End of generated waypoints =====

        self.clear_item(item)
        self.clear_enemy(enemy)

    def Jarilo_GreatMine_F1_X149Y273(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((149.7, 273.5)), | 82.5      | 73       |
        | node     | Waypoint((174.1, 269.0)), | 67.2      | 61       |
        | item     | Waypoint((180.4, 250.8)), | 36.0      | 31       |
        | enemy    | Waypoint((202.4, 256.6)), | 76.4      | 71       |
        | exit     | Waypoint((202.4, 256.6)), | 76.4      | 71       |
        """
        self.map_init(plane=Jarilo_GreatMine, floor="F1", position=(149.7, 273.5))
        self.register_domain_exit(Waypoint((202.4, 256.6)), end_rotation=71)
        node = Waypoint((174.1, 269.0))
        item = Waypoint((180.4, 250.8))
        enemy = Waypoint((202.4, 256.6))
        # ===== End of generated waypoints =====

        # ignore item, bad way
        self.clear_enemy(node, enemy)

    def Jarilo_GreatMine_F1_X407Y572(self):
        """
        | Waypoint        | Position                  | Direction | Rotation |
        | --------------- | ------------------------- | --------- | -------- |
        | spawn           | Waypoint((407.2, 572.8)), | 216.4     | 211      |
        | item1           | Waypoint((382.9, 585.2)), | 263.8     | 260      |
        | enemy1          | Waypoint((382.4, 590.4)), | 241.2     | 239      |
        | item2           | Waypoint((378.2, 610.6)), | 143.8     | 232      |
        | enemy3_X340Y595 | Waypoint((340.6, 595.0)), | 297.8     | 294      |
        | enemy4          | Waypoint((313.1, 575.7)), | 312.1     | 318      |
        | exit            | Waypoint((313.6, 572.6)), | 334.7     | 329      |
        """
        self.map_init(plane=Jarilo_GreatMine, floor="F1", position=(407.2, 572.8))
        self.register_domain_exit(Waypoint((313.6, 572.6)), end_rotation=329)
        item1 = Waypoint((382.9, 585.2))
        enemy1 = Waypoint((382.4, 590.4))
        item2 = Waypoint((378.2, 610.6))
        enemy3_X340Y595 = Waypoint((340.6, 595.0))
        enemy4 = Waypoint((313.1, 575.7))
        # ===== End of generated waypoints =====

        # enemy first
        self.clear_enemy(enemy1)
        self.clear_item(item1)
        self.clear_item(item2)
        # 3
        self.clear_enemy(
            enemy3_X340Y595.straight_run(),
        )
        # 4
        self.clear_enemy(
            enemy4.straight_run(),
        )

    def Jarilo_GreatMine_F1_X485Y450(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((485.4, 450.4)), | 177.8     | 172      |
        | item1    | Waypoint((478.8, 484.8)), | 199.8     | 193      |
        | item2    | Waypoint((488.4, 522.0)), | 175.8     | 170      |
        | enemy3   | Waypoint((465.3, 531.1)), | 92.8      | 232      |
        | enemy5   | Waypoint((546.2, 514.0)), | 45.8      | 225      |
        | enemy4   | Waypoint((512.2, 548.2)), | 59.1      | 59       |
        | item3    | Waypoint((460.3, 570.3)), | 193.0     | 188      |
        | node4    | Waypoint((480.3, 575.6)), | 105.5     | 101      |
        | exit     | Waypoint((549.0, 515.6)), | 112.7     | 15       |
        """
        self.map_init(plane=Jarilo_GreatMine, floor="F1", position=(485.4, 450.4))
        self.register_domain_exit(Waypoint((549.0, 515.6)), end_rotation=15)
        item1 = Waypoint((478.8, 484.8))
        item2 = Waypoint((488.4, 522.0))
        enemy3 = Waypoint((465.3, 531.1))
        enemy5 = Waypoint((546.2, 514.0))
        enemy4 = Waypoint((512.2, 548.2))
        item3 = Waypoint((460.3, 570.3))
        node4 = Waypoint((480.3, 575.6))
        # ===== End of generated waypoints =====

        self.clear_item(item1)
        self.clear_item(item2)
        self.clear_enemy(enemy3.straight_run())
        self.clear_item(item3.straight_run())
        self.clear_enemy(
            node4.straight_run(),
            enemy4.straight_run(),
        )
        self.clear_enemy(enemy5.straight_run())

    def Jarilo_GreatMine_F1_X545Y513(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((545.3, 513.0)), | 222.5     | 218      |
        | item2    | Waypoint((486.8, 523.6)), | 76.5      | 255      |
        | item3    | Waypoint((480.0, 490.2)), | 350.2     | 345      |
        | enemy1   | Waypoint((492.2, 562.0)), | 237.4     | 50       |
        | node2    | Waypoint((468.4, 532.2)), | 30.1      | 27       |
        | enemy3   | Waypoint((485.1, 456.8)), | 102.9     | 4        |
        | node1    | Waypoint((478.5, 576.5)), | 237.2     | 237      |
        | item1    | Waypoint((461.4, 572.2)), | 289.1     | 288      |
        | exit     | Waypoint((485.1, 456.8)), | 102.9     | 4        |
        """
        self.map_init(plane=Jarilo_GreatMine, floor="F1", position=(545.3, 513.0))
        self.register_domain_exit(Waypoint((485.1, 456.8)), end_rotation=4)
        item2 = Waypoint((486.8, 523.6))
        item3 = Waypoint((480.0, 490.2))
        enemy1 = Waypoint((492.2, 562.0))
        node2 = Waypoint((468.4, 532.2))
        enemy3 = Waypoint((485.1, 456.8))
        node1 = Waypoint((478.5, 576.5))
        item1 = Waypoint((461.4, 572.2))
        # ===== End of generated waypoints =====

        # 1
        self.clear_enemy(
            enemy1,
        )
        self.clear_item(
            node1,
            item1.straight_run(),
        )
        # 2
        self.clear_item(
            node2.straight_run(),
            item2,
        )
        # 3
        self.clear_item(
            item3.straight_run(),
        )
        self.clear_enemy(
            enemy3.straight_run(),
        )

    def Jarilo_GreatMine_F1_X84Y378(self):
        """
        | Waypoint | Position                 | Direction | Rotation |
        | -------- | ------------------------ | --------- | -------- |
        | spawn    | Waypoint((84.4, 378.7)), | 334.8     | 331      |
        | item     | Waypoint((60.2, 358.5)), | 319.8     | 308      |
        | enemy    | Waypoint((56.2, 330.8)), | 340.7     | 149      |
        | exit     | Waypoint((57.4, 329.5)), | 22.8      | 334      |
        """
        self.map_init(plane=Jarilo_GreatMine, floor="F1", position=(84.4, 378.7))
        self.register_domain_exit(Waypoint((57.4, 329.5)), end_rotation=334)
        item = Waypoint((60.2, 358.5))
        enemy = Waypoint((56.2, 330.8))
        # ===== End of generated waypoints =====

        self.clear_item(item)
        self.clear_enemy(enemy)
