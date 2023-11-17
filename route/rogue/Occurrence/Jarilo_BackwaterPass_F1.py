from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_BackwaterPass
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_BackwaterPass_F1_X437Y101(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((437.5, 101.5)), | 96.7      | 91       |
        | item     | Waypoint((458.6, 92.2)),  | 67.2      | 57       |
        | event    | Waypoint((476.8, 108.9)), | 103.8     | 96       |
        | exit_    | Waypoint((483.4, 105.3)), | 4.1       | 89       |
        """
        self.map_init(plane=Jarilo_BackwaterPass, floor="F1", position=(437.5, 101.5))
        self.register_domain_exit(Waypoint((483.4, 105.3)), end_rotation=89)
        item = Waypoint((458.6, 92.2))
        event = Waypoint((476.8, 108.9))

        self.clear_item(item)
        self.clear_event(event)
        # ===== End of generated waypoints =====

    def Jarilo_BackwaterPass_F1_X553Y643(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((553.3, 643.5)), | 274.2     | 274      |
        | event    | Waypoint((515.2, 633.2)), | 135.9     | 311      |
        | exit_    | Waypoint((505.0, 642.3)), | 263.8     | 264      |
        | exit1    | Waypoint((499.4, 646.5)), | 277.8     | 274      |
        | exit2    | Waypoint((499.4, 636.2)), | 281.9     | 274      |
        """
        self.map_init(plane=Jarilo_BackwaterPass, floor="F1", position=(553.3, 643.5))
        self.register_domain_exit(
            Waypoint((505.0, 642.3)), end_rotation=264,
            left_door=Waypoint((499.4, 646.5)), right_door=Waypoint((499.4, 636.2)))
        event = Waypoint((515.2, 633.2))

        self.clear_event(event)
        # ===== End of generated waypoints =====

    def Jarilo_BackwaterPass_F1_X613Y755(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((613.3, 755.7)), | 319.8     | 318      |
        | item     | Waypoint((603.0, 734.6)), | 342.6     | 343      |
        | event    | Waypoint((586.8, 724.7)), | 318.0     | 315      |
        | exit_    | Waypoint((576.9, 728.6)), | 126.2     | 304      |
        | exit1    | Waypoint((567.0, 732.7)), | 311.8     | 306      |
        | exit2    | Waypoint((576.2, 722.0)), | 308.1     | 306      |
        """
        self.map_init(plane=Jarilo_BackwaterPass, floor="F1", position=(613.3, 755.7))
        self.register_domain_exit(
            Waypoint((576.9, 728.6)), end_rotation=304,
            left_door=Waypoint((567.0, 732.7)), right_door=Waypoint((576.2, 722.0)))
        item = Waypoint((603.0, 734.6))
        event = Waypoint((586.8, 724.7))

        self.clear_item(item)
        self.clear_event(event)
        # ===== End of generated waypoints =====
