from dataclasses import dataclass

from tasks.map.control.control import MapControl
from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords import MapPlane


@dataclass
class RouteData:
    name: str
    route: str
    plane: str
    floor: str = 'F1'
    position: tuple = None


class RouteBase(MapControl):
    """
    Base class of `Route`
    Every `Route` class must implement method `route()`
    """

    def route_example(self):
        """
        Pages:
            in: page_main
            out: page_main
                Doesn't matter if in/out are not page_main, just be clear what you're doing
        """
        self.map_init(
            plane=...,
            floor=...,
            position=...,
        )
        self.clear_enemy(
            Waypoint(...).run_2x(),
            Waypoint(...),
        )

    def map_init(
            self,
            plane: MapPlane | str,
            floor: str = 'F1',
            position: tuple[int | float, int | float] = None
    ):
        """
        Args:
            plane (MapPlane, str): Such as Jarilo_AdministrativeDistrict
            floor (str):
            position: Initialize the starter point of minimap tracking
                Leaving None will trigger brute-force starter point finding.
        """
        try:
            if self.device.image is None:
                self.device.screenshot()
        except AttributeError:
            self.device.screenshot()

        self.minimap.set_plane(plane, floor=floor)
        if position is not None:
            self.minimap.init_position(position)
