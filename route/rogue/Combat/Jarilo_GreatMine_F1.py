from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_GreatMine
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_GreatMine_F1_X84Y378(self):
        """
        | Waypoint | Position                 | Direction | Rotation |
        | -------- | ------------------------ | --------- | -------- |
        | spawn    | Waypoint((84.4, 378.7)), | 334.8     | 331      |
        | item     | Waypoint((60.2, 358.5)), | 319.8     | 308      |
        | enemy    | Waypoint((60.2, 336.8)), | 340.7     | 149      |
        | exit_    | Waypoint((57.4, 329.5)), | 22.8      | 334      |
        | exit1    | Waypoint((45.4, 329.6)), | 337.2     | 334      |
        | exit2    | Waypoint((61.5, 319.1)), | 337.4     | 336      |
        """
        self.map_init(plane=Jarilo_GreatMine, floor="F1", position=(84.4, 378.7))
        self.register_domain_exit(
            Waypoint((57.4, 329.5)), end_rotation=334,
            left_door=Waypoint((45.4, 329.6)), right_door=Waypoint((61.5, 319.1)))
        item = Waypoint((60.2, 358.5))
        enemy = Waypoint((60.2, 336.8))
        # ===== End of generated waypoints =====

        self.clear_item(item)
        self.clear_enemy(enemy)

    def Jarilo_GreatMine_F1_X91Y391(self):
        """
        | Waypoint | Position                 | Direction | Rotation |
        | -------- | ------------------------ | --------- | -------- |
        | spawn    | Waypoint((91.4, 392.4)), | 334.8     | 331      |
        | item     | Waypoint((60.2, 358.4)), | 308.0     | 304      |
        | enemy    | Waypoint((57.2, 330.8)), | 85.8      | 336      |
        | exit_    | Waypoint((57.2, 330.8)), | 85.8      | 336      |
        | exit1    | Waypoint((45.4, 329.6)), | 337.2     | 334      |
        | exit2    | Waypoint((61.5, 319.1)), | 337.4     | 336      |
        """
        self.map_init(plane=Jarilo_GreatMine, floor="F1", position=(91.4, 392.4))
        self.register_domain_exit(
            Waypoint((57.2, 330.8)), end_rotation=336,
            left_door=Waypoint((45.4, 329.6)), right_door=Waypoint((61.5, 319.1)))
        item = Waypoint((60.2, 358.4))
        enemy = Waypoint((57.2, 330.8))
        # ===== End of generated waypoints =====

        self.clear_item(item)
        self.clear_enemy(enemy)

    def Jarilo_GreatMine_F1_X89Y387(self):
        """
        | Waypoint | Position                 | Direction | Rotation |
        | -------- | ------------------------ | --------- | -------- |
        | spawn    | Waypoint((91.4, 392.4)), | 334.8     | 331      |
        | item     | Waypoint((60.2, 358.4)), | 308.0     | 304      |
        | enemy    | Waypoint((57.2, 330.8)), | 85.8      | 336      |
        | exit_    | Waypoint((57.2, 330.8)), | 85.8      | 336      |
        """
        self.map_init(plane=Jarilo_GreatMine, floor="F1", position=(89.4, 387.6))
        self.register_domain_exit(
            Waypoint((57.2, 330.8)), end_rotation=336,
            left_door=Waypoint((45.4, 329.6)), right_door=Waypoint((61.5, 319.1)))
        item = Waypoint((60.2, 358.4))
        enemy = Waypoint((57.2, 330.8))
        # ===== End of generated waypoints =====

        self.clear_item(item)
        self.clear_enemy(enemy)

        """
        Notes
        Jarilo_GreatMine_F1_X89Y387 is the same as Jarilo_GreatMine_F1_X91Y391
        but for wrong spawn point detected
        """

    def Jarilo_GreatMine_F1_X133Y465(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((133.3, 465.6)), | 334.8     | 331      |
        | item     | Waypoint((108.7, 448.1)), | 318.0     | 320      |
        | enemy    | Waypoint((110.1, 420.6)), | 337.4     | 338      |
        | exit_    | Waypoint((104.0, 414.0)), | 334.8     | 331      |
        | exit1    | Waypoint((97.2, 415.0)),  | 334.8     | 334      |
        | exit2    | Waypoint((108.2, 406.0)), | 334.8     | 334      |
        """
        self.map_init(plane=Jarilo_GreatMine, floor="F1", position=(133.3, 465.6))
        self.register_domain_exit(
            Waypoint((104.0, 414.0)), end_rotation=331,
            left_door=Waypoint((97.2, 415.0)), right_door=Waypoint((108.2, 406.0)))
        item = Waypoint((108.7, 448.1))
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
        | exit_    | Waypoint((202.4, 256.6)), | 76.4      | 71       |
        | exit1    | Waypoint((208.7, 243.8)), | 75.1      | 73       |
        | exit2    | Waypoint((213.2, 263.4)), | 79.8      | 78       |
        """
        self.map_init(plane=Jarilo_GreatMine, floor="F1", position=(149.7, 273.5))
        self.register_domain_exit(
            Waypoint((202.4, 256.6)), end_rotation=71,
            left_door=Waypoint((208.7, 243.8)), right_door=Waypoint((213.2, 263.4)))
        node = Waypoint((174.1, 269.0))
        item = Waypoint((180.4, 250.8))
        enemy = Waypoint((202.4, 256.6))
        # ===== End of generated waypoints =====

        # ignore item, bad way
        self.clear_enemy(node, enemy)

    def Jarilo_GreatMine_F1_X165Y537(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((165.5, 537.8)), | 157.2     | 151      |
        | item1    | Waypoint((174.8, 564.8)), | 190.1     | 184      |
        | enemy1   | Waypoint((218.2, 582.4)), | 129.8     | 304      |
        | node2    | Waypoint((234.0, 586.6)), | 129.8     | 121      |
        | enemy2   | Waypoint((244.8, 626.0)), | 182.7     | 177      |
        | exit_    | Waypoint((243.4, 622.2)), | 2.6       | 174      |
        | exit1    | Waypoint((253.2, 635.3)), | 191.8     | 181      |
        | exit2    | Waypoint((237.6, 635.2)), | 188.8     | 184      |
        """
        self.map_init(plane=Jarilo_GreatMine, floor="F1", position=(165.5, 537.8))
        self.register_domain_exit(
            Waypoint((243.4, 622.2)), end_rotation=174,
            left_door=Waypoint((253.2, 635.3)), right_door=Waypoint((237.6, 635.2)))
        item1 = Waypoint((174.8, 564.8))
        enemy1 = Waypoint((218.2, 582.4))
        node2 = Waypoint((234.0, 586.6))
        enemy2 = Waypoint((244.8, 626.0))
        # ===== End of generated waypoints =====

        # Ignore item1, bad way
        self.clear_enemy(enemy1.straight_run())
        self.clear_enemy(
            node2,
            enemy2.straight_run(),
        )

    def Jarilo_GreatMine_F1_X299Y254(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((299.3, 255.3)), | 274.2     | 274      |
        | item     | Waypoint((282.4, 240.8)), | 295.5     | 292      |
        | enemy    | Waypoint((246.2, 248.4)), | 282.8     | 281      |
        | exit_    | Waypoint((246.6, 248.8)), | 96.8      | 274      |
        | exit1    | Waypoint((235.7, 255.9)), | 281.9     | 274      |
        | exit2    | Waypoint((237.4, 239.4)), | 281.9     | 276      |
        """
        self.map_init(plane=Jarilo_GreatMine, floor="F1", position=(299.3, 255.3))
        self.register_domain_exit(
            Waypoint((246.6, 248.8)), end_rotation=274,
            left_door=Waypoint((235.7, 255.9)), right_door=Waypoint((237.4, 239.4)))
        item = Waypoint((282.4, 240.8))
        enemy = Waypoint((246.2, 248.4))
        # ===== End of generated waypoints =====

        # Ignore item, bad way
        self.clear_enemy(enemy)

    def Jarilo_GreatMine_F1_X407Y572(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((407.2, 572.8)), | 216.4     | 211      |
        | item1    | Waypoint((382.9, 585.3)), | 263.8     | 260      |
        | enemy1   | Waypoint((382.4, 590.4)), | 241.2     | 239      |
        | item2    | Waypoint((378.2, 610.6)), | 143.8     | 232      |
        | enemy3   | Waypoint((339.0, 595.4)), | 297.8     | 294      |
        | enemy4   | Waypoint((312.7, 575.6)), | 312.1     | 318      |
        | exit_    | Waypoint((315.6, 572.6)), | 334.7     | 329      |
        | exit1    | Waypoint((301.0, 565.9)), | 332.8     | 327      |
        | exit2    | Waypoint((313.4, 561.4)), | 337.2     | 334      |
        """
        self.map_init(plane=Jarilo_GreatMine, floor="F1", position=(407.2, 572.8))
        self.register_domain_exit(
            Waypoint((315.6, 572.6)), end_rotation=329,
            left_door=Waypoint((301.0, 565.9)), right_door=Waypoint((313.4, 561.4)))
        item1 = Waypoint((382.9, 585.3))
        enemy1 = Waypoint((382.4, 590.4))
        item2 = Waypoint((378.2, 610.6))
        enemy3 = Waypoint((339.0, 595.4))
        enemy4 = Waypoint((312.7, 575.6))
        # ===== End of generated waypoints =====

        # enemy first
        self.clear_enemy(enemy1)
        # item1 is too close to enemy1, usually to be destroyed along with enemy1
        # self.clear_item(item1)
        self.clear_item(item2)
        # 3
        self.clear_enemy(
            enemy3.straight_run(),
        )
        # 4
        self.clear_enemy(
            enemy4.straight_run(),
        )

    def Jarilo_GreatMine_F1_X485Y450(self):
        """
        | Waypoint   | Position                  | Direction | Rotation |
        | ---------- | ------------------------- | --------- | -------- |
        | spawn      | Waypoint((485.5, 450.4)), | 177.8     | 172      |
        | item1      | Waypoint((478.8, 484.8)), | 199.8     | 193      |
        | item2      | Waypoint((488.4, 522.0)), | 175.8     | 170      |
        | enemy3top  | Waypoint((465.3, 531.1)), | 92.8      | 232      |
        | enemy5     | Waypoint((546.2, 514.0)), | 45.8      | 225      |
        | enemy4     | Waypoint((512.2, 548.2)), | 59.1      | 59       |
        | enemy3down | Waypoint((453.3, 559.2)), | 129.8     | 218      |
        | item3      | Waypoint((460.3, 570.3)), | 193.0     | 188      |
        | node4      | Waypoint((480.3, 575.6)), | 105.5     | 101      |
        | exit_      | Waypoint((549.0, 515.6)), | 112.7     | 15       |
        | exit1      | Waypoint((542.6, 502.6)), | 21.0      | 15       |
        | exit2      | Waypoint((556.2, 509.4)), | 30.1      | 27       |
        """
        self.map_init(plane=Jarilo_GreatMine, floor="F1", position=(485.5, 450.4))
        self.register_domain_exit(
            Waypoint((549.0, 515.6)), end_rotation=15,
            left_door=Waypoint((542.6, 502.6)), right_door=Waypoint((556.2, 509.4)))
        item1 = Waypoint((478.8, 484.8))
        item2 = Waypoint((488.4, 522.0))
        enemy3top = Waypoint((465.3, 531.1))
        enemy5 = Waypoint((546.2, 514.0))
        enemy4 = Waypoint((512.2, 548.2))
        enemy3down = Waypoint((453.3, 559.2))
        item3 = Waypoint((460.3, 570.3))
        node4 = Waypoint((480.3, 575.6))
        # ===== End of generated waypoints =====

        self.clear_item(item1)
        self.rotation_set(232)
        self.clear_enemy(
            item2,
            enemy3top,
            enemy3down,
        )
        # self.clear_item(item3.straight_run())
        self.clear_enemy(
            item3.straight_run(),
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
        | enemy2   | Waypoint((478.3, 519.6)), | 21.0      | 18       |
        | item3    | Waypoint((480.0, 490.2)), | 350.2     | 345      |
        | enemy1   | Waypoint((492.2, 562.0)), | 237.4     | 50       |
        | enemy3   | Waypoint((485.1, 456.8)), | 102.9     | 4        |
        | node1    | Waypoint((478.5, 576.5)), | 237.2     | 237      |
        | item1    | Waypoint((461.4, 572.2)), | 289.1     | 288      |
        | exit_    | Waypoint((485.1, 456.8)), | 102.9     | 4        |
        | exit1    | Waypoint((475.2, 449.0)), | 4.1       | 359      |
        | exit2    | Waypoint((490.6, 449.2)), | 4.1       | 359      |
        """
        self.map_init(plane=Jarilo_GreatMine, floor="F1", position=(545.3, 513.0))
        self.register_domain_exit(
            Waypoint((485.1, 456.8)), end_rotation=4,
            left_door=Waypoint((475.2, 449.0)), right_door=Waypoint((490.6, 449.2)))
        item2 = Waypoint((486.8, 523.6))
        enemy2 = Waypoint((478.3, 519.6))
        item3 = Waypoint((480.0, 490.2))
        enemy1 = Waypoint((492.2, 562.0))
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
        # 2, ignore item2, bad way
        self.goto(
            enemy2.straight_run()
        )
        # 3
        self.clear_item(
            item3.straight_run(),
        )
        self.clear_enemy(
            enemy3.straight_run(),
        )
