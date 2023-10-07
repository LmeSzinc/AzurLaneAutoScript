from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_StargazerNavalia
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_StargazerNavalia_F2Rogue_X569Y275(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((574.8, 275.0)), | 256.7     | 253      |
        | item     | Waypoint((553.4, 273.2)), | 294.6     | 292      |
        | herta    | Waypoint((533.4, 286.9)), | 271.8     | 269      |
        | exit     | Waypoint((515.4, 299.2)), | 239.8     | 239      |
        """
        self.map_init(plane=Luofu_StargazerNavalia, floor="F2Rogue", position=(569, 275.0))
        item = Waypoint((553.4, 273.2))
        herta = Waypoint((533.4, 286.9))
        exit_ = Waypoint((515.4, 299.2))

        self.clear_item(item)
        self.domain_herta(herta)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====

        """
        Notes
        Luofu_StargazerNavalia_F2Rogue_X569Y275 is the same as Luofu_StargazerNavalia_F2Rogue_X574Y275
        but for wrong spawn point detected
        """

    def Luofu_StargazerNavalia_F2Rogue_X574Y275(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((574.8, 275.0)), | 256.7     | 253      |
        | item     | Waypoint((553.4, 273.2)), | 294.6     | 292      |
        | herta    | Waypoint((533.4, 286.9)), | 271.8     | 269      |
        | exit     | Waypoint((515.4, 299.2)), | 239.8     | 239      |
        """
        self.map_init(plane=Luofu_StargazerNavalia, floor="F2Rogue", position=(574.8, 275.0))
        item = Waypoint((553.4, 273.2))
        herta = Waypoint((533.4, 286.9))
        exit_ = Waypoint((515.4, 299.2))

        self.clear_item(item)
        self.domain_herta(herta)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====
