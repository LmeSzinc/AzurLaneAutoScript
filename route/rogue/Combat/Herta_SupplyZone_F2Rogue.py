from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Herta_SupplyZone
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Herta_SupplyZone_F2Rogue_X209Y112(self):
        """
        | Waypoint       | Position                  | Direction | Rotation |
        | -------------- | ------------------------- | --------- | -------- |
        | spawn          | Waypoint((219.6, 112.8)), | 96.7      | 91       |
        | item           | Waypoint((227.4, 105.1)), | 67.2      | 61       |
        | enemy          | Waypoint((264.2, 114.1)), | 101.1     | 98       |
        | exit_          | Waypoint((266.7, 113.7)), | 60.8      | 91       |
        | exit1_X269Y105 | Waypoint((269.7, 105.7)), | 101.1     | 91       |
        | exit2_X273Y119 | Waypoint((273.0, 119.2)), | 101.1     | 91       |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2Rogue", position=(209.6, 112.8))
        self.register_domain_exit(
            Waypoint((266.7, 113.7)), end_rotation=91,
            left_door=Waypoint((269.7, 105.7)), right_door=Waypoint((273.0, 119.2)))
        item = Waypoint((227.4, 105.1))
        enemy = Waypoint((264.2, 114.1))
        # ===== End of generated waypoints =====

        """
        Notes:
        Herta_SupplyZone_F2Rogue_X209Y112 is the same as Herta_SupplyZone_F2Rogue_X219Y112 to handle detection errors
        """
        self.register_domain_exit(
            Waypoint((266.7, 113.7)), end_rotation=91,
            left_door=Waypoint((270.7, 105.7)), right_door=Waypoint((270.7, 119.2)))
        self.clear_item(item)
        self.clear_enemy(enemy)

    def Herta_SupplyZone_F2Rogue_X215Y112(self):
        """
        | Waypoint       | Position                  | Direction | Rotation |
        | -------------- | ------------------------- | --------- | -------- |
        | spawn          | Waypoint((219.6, 112.8)), | 96.7      | 91       |
        | item           | Waypoint((227.4, 105.1)), | 67.2      | 61       |
        | enemy          | Waypoint((264.2, 114.1)), | 101.1     | 98       |
        | exit_          | Waypoint((266.7, 113.7)), | 60.8      | 91       |
        | exit1_X269Y105 | Waypoint((269.7, 105.7)), | 101.1     | 91       |
        | exit2_X273Y119 | Waypoint((273.0, 119.2)), | 101.1     | 91       |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2Rogue", position=(215.6, 112.8))
        self.register_domain_exit(
            Waypoint((266.7, 113.7)), end_rotation=91,
            left_door=Waypoint((269.7, 105.7)), right_door=Waypoint((273.0, 119.2)))
        item = Waypoint((227.4, 105.1))
        enemy = Waypoint((264.2, 114.1))
        # ===== End of generated waypoints =====

        """
        Notes:
        Herta_SupplyZone_F2Rogue_X215Y112 is the same as Herta_SupplyZone_F2Rogue_X219Y112 to handle detection errors
        """
        self.register_domain_exit(
            Waypoint((266.7, 113.7)), end_rotation=91,
            left_door=Waypoint((270.7, 105.7)), right_door=Waypoint((270.7, 119.2)))
        self.clear_item(item)
        self.clear_enemy(enemy)

    def Herta_SupplyZone_F2Rogue_X219Y112(self):
        """
        | Waypoint       | Position                  | Direction | Rotation |
        | -------------- | ------------------------- | --------- | -------- |
        | spawn          | Waypoint((219.6, 112.8)), | 96.7      | 91       |
        | item           | Waypoint((227.4, 105.1)), | 67.2      | 61       |
        | enemy          | Waypoint((264.2, 114.1)), | 101.1     | 98       |
        | exit_          | Waypoint((266.7, 113.7)), | 60.8      | 91       |
        | exit1_X269Y105 | Waypoint((269.7, 105.7)), | 101.1     | 91       |
        | exit2_X273Y119 | Waypoint((273.0, 119.2)), | 101.1     | 91       |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2Rogue", position=(219.6, 112.8))
        self.register_domain_exit(
            Waypoint((266.7, 113.7)), end_rotation=91,
            left_door=Waypoint((269.7, 105.7)), right_door=Waypoint((273.0, 119.2)))
        item = Waypoint((227.4, 105.1))
        enemy = Waypoint((264.2, 114.1))
        # ===== End of generated waypoints =====

        self.register_domain_exit(
            Waypoint((266.7, 113.7)), end_rotation=91,
            left_door=Waypoint((270.7, 105.7)), right_door=Waypoint((270.7, 119.2)))
        self.clear_item(item)
        self.clear_enemy(enemy)
