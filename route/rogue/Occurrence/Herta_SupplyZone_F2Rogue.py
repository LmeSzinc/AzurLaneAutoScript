from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Herta_SupplyZone
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Herta_SupplyZone_F2Rogue_X209Y113(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((219.6, 113.1)), | 96.7      | 91       |
        | item     | Waypoint((230.9, 106.7)), | 326.8     | 80       |
        | event    | Waypoint((256.6, 118.2)), | 96.8      | 96       |
        | exit     | Waypoint((262.5, 112.9)), | 96.7      | 91       |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2Rogue", position=(209.6, 113.1))
        self.register_domain_exit(Waypoint((262.5, 112.9)), end_rotation=91)
        item = Waypoint((230.9, 106.7))
        event = Waypoint((256.6, 118.2))

        self.clear_item(item)
        self.clear_event(event)
        # ===== End of generated waypoints =====

        """
        Notes
        Herta_SupplyZone_F2Rogue_X209Y113 is the same as Herta_SupplyZone_F2Rogue_X219Y113
        but for wrong spawn point detected
        """

    def Herta_SupplyZone_F2Rogue_X214Y113(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((219.6, 113.1)), | 96.7      | 91       |
        | item     | Waypoint((230.9, 106.7)), | 326.8     | 80       |
        | event    | Waypoint((256.6, 118.2)), | 96.8      | 96       |
        | exit     | Waypoint((262.5, 112.9)), | 96.7      | 91       |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2Rogue", position=(214.6, 113.1))
        self.register_domain_exit(Waypoint((262.5, 112.9)), end_rotation=91)
        item = Waypoint((230.9, 106.7))
        event = Waypoint((256.6, 118.2))

        self.clear_item(item)
        self.clear_event(event)
        # ===== End of generated waypoints =====

        """
        Notes
        Herta_SupplyZone_F2Rogue_X214Y113 is the same as Herta_SupplyZone_F2Rogue_X219Y113
        but for wrong spawn point detected
        """

    def Herta_SupplyZone_F2Rogue_X219Y113(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((219.6, 113.1)), | 96.7      | 91       |
        | item     | Waypoint((230.9, 106.7)), | 326.8     | 80       |
        | event    | Waypoint((256.6, 118.2)), | 96.8      | 96       |
        | exit     | Waypoint((262.5, 112.9)), | 96.7      | 91       |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2Rogue", position=(219.6, 113.1))
        self.register_domain_exit(Waypoint((262.5, 112.9)), end_rotation=91)
        item = Waypoint((230.9, 106.7))
        event = Waypoint((256.6, 118.2))

        self.clear_item(item)
        self.clear_event(event)
        # ===== End of generated waypoints =====

    def Herta_SupplyZone_F2Rogue_X397Y227(self):
        """
        | Waypoint       | Position                  | Direction | Rotation |
        | -------------- | ------------------------- | --------- | -------- |
        | spawn          | Waypoint((397.4, 235.3)), | 6.7       | 4        |
        | event_X404Y182 | Waypoint((404.5, 182.1)), | 26.8      | 24       |
        | exit_X398Y173  | Waypoint((398.6, 173.0)), | 4.2       | 1        |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2Rogue", position=(397.4, 227))
        self.register_domain_exit(Waypoint((398.6, 173.0)), end_rotation=1)
        event_X404Y182 = Waypoint((404.5, 182.1))

        self.clear_event(event_X404Y182)
        # ===== End of generated waypoints =====

        """
        Notes
        Herta_SupplyZone_F2Rogue_X397Y227 is the same as Herta_SupplyZone_F2Rogue_X397Y235
        but for wrong spawn point detected
        """

    def Herta_SupplyZone_F2Rogue_X397Y230(self):
        """
        | Waypoint       | Position                  | Direction | Rotation |
        | -------------- | ------------------------- | --------- | -------- |
        | spawn          | Waypoint((397.4, 235.3)), | 6.7       | 4        |
        | event_X404Y182 | Waypoint((404.5, 182.1)), | 26.8      | 24       |
        | exit_X398Y173  | Waypoint((398.6, 173.0)), | 4.2       | 1        |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2Rogue", position=(397.4, 230))
        self.register_domain_exit(Waypoint((398.6, 173.0)), end_rotation=1)
        event_X404Y182 = Waypoint((404.5, 182.1))

        self.clear_event(event_X404Y182)
        # ===== End of generated waypoints =====

        """
        Notes
        Herta_SupplyZone_F2Rogue_X397Y230 is the same as Herta_SupplyZone_F2Rogue_X397Y235
        but for wrong spawn point detected
        """

    def Herta_SupplyZone_F2Rogue_X397Y235(self):
        """
        | Waypoint       | Position                  | Direction | Rotation |
        | -------------- | ------------------------- | --------- | -------- |
        | spawn          | Waypoint((397.4, 235.3)), | 6.7       | 4        |
        | event_X404Y182 | Waypoint((404.5, 182.1)), | 26.8      | 24       |
        | exit_X398Y173  | Waypoint((398.6, 173.0)), | 4.2       | 1        |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2Rogue", position=(397.4, 235.3))
        self.register_domain_exit(Waypoint((398.6, 173.0)), end_rotation=1)
        event_X404Y182 = Waypoint((404.5, 182.1))

        self.clear_event(event_X404Y182)
        # ===== End of generated waypoints =====
